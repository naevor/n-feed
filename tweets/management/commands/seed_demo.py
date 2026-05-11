import random

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from tweets.models import Comment, Tweet

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users, tweets, follows, likes, comments, tags, and mentions."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=20)
        parser.add_argument("--tweets", type=int, default=200)
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo users before seeding.",
        )

    def handle(self, *args, **options):
        users_count = options["users"]
        tweets_count = options["tweets"]

        if users_count < 1:
            raise CommandError("--users must be at least 1.")
        if tweets_count < 0:
            raise CommandError("--tweets must not be negative.")

        rng = random.Random(options["seed"])

        if options["reset"]:
            User.objects.filter(username__startswith="demo_user_").delete()

        users = self._create_users(count=users_count)
        self._create_follows(users=users, rng=rng)
        tweets = self._create_tweets(users=users, count=tweets_count, rng=rng)
        comments_count, likes_count = self._create_activity(users=users, tweets=tweets, rng=rng)

        cache.clear()
        self.stdout.write(
            self.style.SUCCESS(
                "Seeded "
                f"{len(users)} users, {len(tweets)} tweets, "
                f"{likes_count} likes, {comments_count} comments."
            )
        )

    def _create_users(self, *, count):
        users = []
        for index in range(1, count + 1):
            username = f"demo_user_{index}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "bio": f"Demo profile for {username}.",
                },
            )
            if created:
                user.set_password("demo-pass")
                user.save(update_fields=["password"])
            users.append(user)
        return users

    def _create_follows(self, *, users, rng):
        if len(users) < 2:
            return

        for user in users:
            candidates = [candidate for candidate in users if candidate.pk != user.pk]
            follow_count = rng.randint(0, min(5, len(candidates)))
            if follow_count:
                user.following.add(*rng.sample(candidates, follow_count))

    def _create_tweets(self, *, users, count, rng):
        openers = [
            "Building",
            "Testing",
            "Shipping",
            "Debugging",
            "Reading",
            "Refactoring",
        ]
        topics = [
            "Django APIs",
            "clean services",
            "fast selectors",
            "docker deploys",
            "pytest coverage",
            "product ideas",
        ]
        tags = ["django", "python", "api", "dev", "backend", "nfeed"]

        tweets = []
        for _ in range(count):
            author = rng.choice(users)
            mentioned = rng.choice(users)
            content = (
                f"{rng.choice(openers)} {rng.choice(topics)} "
                f"with @{mentioned.username} #{rng.choice(tags)}"
            )
            tweets.append(Tweet.objects.create(user=author, content=content))
        return tweets

    def _create_activity(self, *, users, tweets, rng):
        comments = [
            "Looks good.",
            "Need to test this.",
            "Nice progress.",
            "Ship it.",
            "Worth documenting.",
        ]
        comments_count = 0
        likes_count = 0

        for tweet in tweets:
            possible_likers = [user for user in users if user.pk != tweet.user_id]
            like_count = rng.randint(0, min(8, len(possible_likers)))
            if like_count:
                likers = rng.sample(possible_likers, like_count)
                tweet.likes.add(*likers)
                likes_count += len(likers)

            for _ in range(rng.randint(0, 3)):
                Comment.objects.create(
                    tweet=tweet,
                    user=rng.choice(users),
                    content=rng.choice(comments),
                )
                comments_count += 1

        return comments_count, likes_count

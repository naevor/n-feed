(() => {
    const container = document.querySelector("[data-feed-container]");
    const list = document.querySelector("[data-feed-list]");
    if (!container || !list || !("WebSocket" in window)) {
        return;
    }

    const emptyState = document.querySelector("[data-feed-empty]");
    const defaultAvatarUrl = container.dataset.defaultAvatarUrl || "";
    const seenTweetIds = new Set(
        Array.from(list.querySelectorAll("[data-tweet-id]")).map((item) => item.dataset.tweetId)
    );

    const createText = (tagName, className, text) => {
        const element = document.createElement(tagName);
        if (className) {
            element.className = className;
        }
        element.textContent = text || "";
        return element;
    };

    const createTweetCard = (tweet) => {
        const item = document.createElement("li");
        item.className = "tweet-card tweet-card-live";
        item.dataset.tweetId = String(tweet.id);

        const header = document.createElement("div");
        header.className = "tweet-header";

        const author = document.createElement("a");
        author.className = "tweet-author";
        author.href = tweet.user?.profile_url || "#";

        const avatar = document.createElement("img");
        avatar.className = "avatar";
        avatar.alt = "Avatar";
        avatar.src = tweet.user?.avatar_url || defaultAvatarUrl;

        const username = createText("span", "", tweet.user?.username || "unknown");
        author.append(avatar, username);

        const date = createText("span", "tweet-date", tweet.created_at);
        header.append(author, date);

        const content = createText("p", "tweet-content", tweet.content);
        item.append(header, content);

        if (tweet.media_url) {
            const media = document.createElement("img");
            media.className = "tweet-media";
            media.alt = "Tweet Media";
            media.src = tweet.media_url;
            item.appendChild(media);
        }

        const actions = document.createElement("div");
        actions.className = "tweet-actions";

        const openLink = document.createElement("a");
        openLink.className = "btn";
        openLink.href = tweet.tweet_url || "#";
        openLink.textContent = "Open";
        actions.appendChild(openLink);
        item.appendChild(actions);

        return item;
    };

    const insertTweet = (tweet) => {
        if (!tweet?.id || seenTweetIds.has(String(tweet.id))) {
            return;
        }

        seenTweetIds.add(String(tweet.id));
        list.hidden = false;
        if (emptyState) {
            emptyState.hidden = true;
        }
        list.prepend(createTweetCard(tweet));
    };

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/feed/`);

    socket.addEventListener("message", (event) => {
        let message;
        try {
            message = JSON.parse(event.data);
        } catch {
            return;
        }

        if (message.type === "tweet.created") {
            insertTweet(message.tweet);
        }
    });
})();

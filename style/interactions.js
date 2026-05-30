(() => {
    const forms = document.querySelectorAll("[data-tweet-interaction]");
    if (!forms.length || !("fetch" in window)) {
        return;
    }

    const currentUserId = document.querySelector("[data-current-user-id]")?.dataset.currentUserId;

    const updateTweetCards = (payload) => {
        const tweetId = payload?.tweet_id;
        if (!tweetId) {
            return;
        }

        document.querySelectorAll(`[data-tweet-id="${tweetId}"]`).forEach((card) => {
            if (Number.isInteger(payload.likes_count)) {
                card.querySelectorAll("[data-like-count]").forEach((element) => {
                    element.textContent = String(payload.likes_count);
                });
            }

            let likeLabel = payload.like_label;
            if (
                !likeLabel &&
                String(payload.actor_user_id) === currentUserId &&
                typeof payload.liked === "boolean"
            ) {
                likeLabel = payload.liked ? "Unlike" : "Like";
            }

            if (likeLabel) {
                card.querySelectorAll("[data-like-label]").forEach((element) => {
                    element.textContent = likeLabel;
                });
            }

            if (payload.bookmark_label) {
                card.querySelectorAll("[data-bookmark-label]").forEach((element) => {
                    element.textContent = payload.bookmark_label;
                });
            }
        });
    };

    const setFormPending = (form, pending) => {
        form.querySelectorAll("button").forEach((button) => {
            button.disabled = pending;
            button.setAttribute("aria-busy", pending ? "true" : "false");
        });
    };

    const submitForm = async (form) => {
        setFormPending(form, true);
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            if (!response.ok) {
                window.location.reload();
                return;
            }

            const payload = await response.json();
            updateTweetCards(payload);
        } catch {
            window.location.reload();
        } finally {
            setFormPending(form, false);
        }
    };

    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            submitForm(form);
        });
    });

    window.nFeedUpdateTweetInteractions = updateTweetCards;
})();

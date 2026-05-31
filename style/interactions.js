(() => {
    const forms = document.querySelectorAll("[data-tweet-interaction]");
    const commentForms = document.querySelectorAll("[data-comment-form]");
    if ((!forms.length && !commentForms.length) || !("fetch" in window)) {
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

    const knownCommentIds = new Set(
        Array.from(document.querySelectorAll("[data-comment-id]")).map(
            (element) => element.dataset.commentId
        )
    );

    const insertComment = (comment) => {
        if (!comment?.id || knownCommentIds.has(String(comment.id))) {
            return;
        }

        const list = document.querySelector(`[data-comment-list][data-tweet-id="${comment.tweet_id}"]`);
        if (!list) {
            return;
        }

        knownCommentIds.add(String(comment.id));
        list.querySelector("[data-comment-empty]")?.remove();

        const item = document.createElement("li");
        item.className = "comment-card";
        item.dataset.commentId = String(comment.id);

        const header = document.createElement("div");
        header.className = "comment-header";

        const username = document.createElement("strong");
        username.textContent = comment.user?.username || "unknown";

        const createdAt = document.createElement("span");
        createdAt.textContent = comment.created_at || "";

        const content = document.createElement("p");
        if (comment.content_html) {
            content.innerHTML = comment.content_html;
        } else {
            content.textContent = comment.content || "";
        }

        header.append(username, createdAt);
        item.append(header, content);
        list.prepend(item);
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

    const submitCommentForm = async (form) => {
        const error = form.querySelector("[data-comment-error]");
        if (error) {
            error.hidden = true;
            error.textContent = "";
        }

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
                const payload = await response.json().catch(() => null);
                if (error && payload?.errors) {
                    error.textContent = Object.values(payload.errors).flat().join(" ");
                    error.hidden = false;
                    return;
                }
                window.location.reload();
                return;
            }

            const payload = await response.json();
            insertComment(payload.comment);
            form.reset();
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

    commentForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            submitCommentForm(form);
        });
    });

    window.nFeedUpdateTweetInteractions = updateTweetCards;
    window.nFeedInsertComment = insertComment;
})();

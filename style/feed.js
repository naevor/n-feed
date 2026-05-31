(() => {
    const container = document.querySelector("[data-feed-container]");
    const list = document.querySelector("[data-feed-list]");
    const hasFeed = Boolean(container && list);
    const hasTweetInteractions = Boolean(document.querySelector("[data-tweet-interaction]"));
    if ((!hasFeed && !hasTweetInteractions) || !("WebSocket" in window)) {
        return;
    }

    const emptyState = hasFeed ? document.querySelector("[data-feed-empty]") : null;
    const defaultAvatarUrl = container?.dataset.defaultAvatarUrl || "";
    const seenTweetIds = new Set(
        hasFeed
            ? Array.from(list.querySelectorAll("[data-tweet-id]")).map((item) => item.dataset.tweetId)
            : []
    );
    const reconnectBaseDelayMs = 1000;
    const reconnectMaxDelayMs = 30000;
    let reconnectAttempts = 0;
    let reconnectTimer = null;
    let socket = null;

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
        if (!hasFeed || !tweet?.id || seenTweetIds.has(String(tweet.id))) {
            return;
        }

        seenTweetIds.add(String(tweet.id));
        list.hidden = false;
        if (emptyState) {
            emptyState.hidden = true;
        }
        list.prepend(createTweetCard(tweet));
    };

    const handleMessage = (event) => {
        let message;
        try {
            message = JSON.parse(event.data);
        } catch {
            return;
        }

        if (message.type === "tweet.created") {
            insertTweet(message.tweet);
            return;
        }

        if (message.type === "tweet.likes_changed") {
            window.nFeedUpdateTweetInteractions?.(message.tweet);
            return;
        }

        if (message.type === "tweet.comment_created") {
            window.nFeedInsertComment?.(message.comment);
        }
    };

    const scheduleReconnect = () => {
        if (reconnectTimer || document.hidden) {
            return;
        }

        const delay = Math.min(
            reconnectBaseDelayMs * 2 ** reconnectAttempts,
            reconnectMaxDelayMs
        );
        reconnectAttempts += 1;
        reconnectTimer = window.setTimeout(() => {
            reconnectTimer = null;
            connect();
        }, delay);
    };

    const connect = () => {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        socket = new WebSocket(`${protocol}://${window.location.host}/ws/feed/`);

        socket.addEventListener("open", () => {
            reconnectAttempts = 0;
        });
        socket.addEventListener("message", handleMessage);
        socket.addEventListener("close", scheduleReconnect);
        socket.addEventListener("error", () => {
            socket.close();
        });
    };

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden && (!socket || socket.readyState === WebSocket.CLOSED)) {
            scheduleReconnect();
        }
    });

    connect();
})();

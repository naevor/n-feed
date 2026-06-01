(() => {
    const badge = document.querySelector("[data-notification-badge]");
    const toastStack = document.querySelector("[data-toast-stack]");
    if (!badge || !toastStack) {
        return;
    }

    const list = document.querySelector("[data-notification-list]");
    const emptyState = document.querySelector("[data-notification-empty]");
    const markAllForm = document.querySelector('[data-notification-action="mark-all-read"]');
    const knownNotificationIds = new Set(
        Array.from(document.querySelectorAll("[data-notification-id]")).map(
            (element) => element.dataset.notificationId
        )
    );
    const reconnectBaseDelayMs = 1000;
    const reconnectMaxDelayMs = 30000;
    let reconnectAttempts = 0;
    let reconnectTimer = null;
    let socket = null;

    const setBadgeCount = (count) => {
        const normalizedCount = Math.max(Number.parseInt(count || "0", 10) || 0, 0);
        badge.dataset.count = String(normalizedCount);
        badge.textContent = String(normalizedCount);
        badge.hidden = normalizedCount === 0;
    };

    const incrementBadge = () => {
        const currentCount = Number.parseInt(badge.dataset.count || "0", 10);
        setBadgeCount(Number.isNaN(currentCount) ? 1 : currentCount + 1);
    };

    const notificationText = (notification) => {
        const actor = notification?.actor?.username || "Someone";
        const labels = {
            like: "liked your tweet",
            comment: "commented on your tweet",
            follow: "followed you",
            mention: "mentioned you",
        };
        return `${actor} ${labels[notification?.kind] || "sent a notification"}`;
    };

    const notificationDetailUrl = (notification) => {
        if (notification?.tweet_slug) {
            return `/tweets/${encodeURIComponent(notification.tweet_slug)}/`;
        }
        if (notification?.actor?.username) {
            return `/users/profile/${encodeURIComponent(notification.actor.username)}/`;
        }
        return "/notifications/";
    };

    const csrfToken = () => {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    };

    const syncMarkAllVisibility = () => {
        if (!markAllForm) {
            return;
        }
        const hasUnread = Boolean(document.querySelector(".notification-card.unread"));
        markAllForm.hidden = !hasUnread;
    };

    const markCardRead = (notificationId) => {
        const card = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (!card) {
            return;
        }
        card.classList.remove("unread");
        card.querySelector('[data-notification-action="mark-read"]')?.remove();
        syncMarkAllVisibility();
    };

    const markAllCardsRead = () => {
        document.querySelectorAll(".notification-card.unread").forEach((card) => {
            card.classList.remove("unread");
            card.querySelector('[data-notification-action="mark-read"]')?.remove();
        });
        syncMarkAllVisibility();
    };

    const createMarkReadForm = (notification) => {
        const form = document.createElement("form");
        form.method = "post";
        form.action = `/notifications/${notification.id}/mark-read/`;
        form.className = "notification-action";
        form.dataset.notificationAction = "mark-read";

        const button = document.createElement("button");
        button.type = "submit";
        button.className = "btn";
        button.textContent = "Mark read";
        form.appendChild(button);
        return form;
    };

    const insertNotification = (notification) => {
        if (!list || !notification?.id || knownNotificationIds.has(String(notification.id))) {
            return;
        }

        knownNotificationIds.add(String(notification.id));
        list.hidden = false;
        if (emptyState) {
            emptyState.hidden = true;
        }

        const item = document.createElement("li");
        item.className = "notification-card unread";
        item.dataset.notificationId = String(notification.id);

        const body = document.createElement("div");
        body.className = "notification-body";

        const actor = document.createElement("a");
        actor.href = notification?.actor?.username
            ? `/users/profile/${encodeURIComponent(notification.actor.username)}/`
            : "/notifications/";
        actor.textContent = notification?.actor?.username || "Someone";

        const message = document.createElement("span");
        message.textContent = ` ${notificationText(notification).replace(
            notification?.actor?.username || "Someone",
            ""
        ).trim()}`;

        body.append(actor, message);
        if (notification.tweet_slug) {
            const tweet = document.createElement("p");
            const tweetLink = document.createElement("a");
            tweetLink.href = notificationDetailUrl(notification);
            tweetLink.textContent = notification.tweet_content || "Open tweet";
            tweet.appendChild(tweetLink);
            body.appendChild(tweet);
        }

        const createdAt = document.createElement("small");
        createdAt.textContent = notification.created_at || "";
        body.appendChild(createdAt);

        item.append(body, createMarkReadForm(notification));
        list.prepend(item);
        syncMarkAllVisibility();
    };

    const showToast = (notification) => {
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = notificationText(notification);
        toastStack.appendChild(toast);
        window.setTimeout(() => toast.remove(), 5000);
    };

    const handleMessage = (event) => {
        let message;
        try {
            message = JSON.parse(event.data);
        } catch {
            return;
        }
        if (message.type === "notification.created") {
            incrementBadge();
            insertNotification(message.notification);
            showToast(message.notification);
            return;
        }

        if (message.type === "notification.unread_count") {
            setBadgeCount(message.unread_count);
        }
    };

    const setFormPending = (form, pending) => {
        form.querySelectorAll("button").forEach((button) => {
            button.disabled = pending;
            button.setAttribute("aria-busy", pending ? "true" : "false");
        });
    };

    const submitNotificationAction = async (form) => {
        setFormPending(form, true);
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-CSRFToken": csrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            if (!response.ok) {
                window.location.reload();
                return;
            }

            const payload = await response.json();
            setBadgeCount(payload.unread_count);

            if (form.dataset.notificationAction === "mark-all-read") {
                markAllCardsRead();
                return;
            }

            if (payload.notification_id) {
                markCardRead(payload.notification_id);
            }
        } catch {
            window.location.reload();
        } finally {
            setFormPending(form, false);
        }
    };

    if ("fetch" in window) {
        document.addEventListener("submit", (event) => {
            const form = event.target.closest("[data-notification-action]");
            if (!form) {
                return;
            }

            event.preventDefault();
            submitNotificationAction(form);
        });
    }

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

    if (!("WebSocket" in window)) {
        return;
    }

    const connect = () => {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/`);

        socket.addEventListener("open", () => {
            reconnectAttempts = 0;
        });
        socket.addEventListener("message", handleMessage);
        socket.addEventListener("close", (event) => {
            if (event.code !== 4401) {
                scheduleReconnect();
            }
        });
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

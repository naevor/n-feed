(() => {
    const badge = document.querySelector("[data-notification-badge]");
    const toastStack = document.querySelector("[data-toast-stack]");
    if (!badge || !toastStack || !("WebSocket" in window)) {
        return;
    }

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
            showToast(message.notification);
            return;
        }

        if (message.type === "notification.unread_count") {
            setBadgeCount(message.unread_count);
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

(() => {
    const badge = document.querySelector("[data-notification-badge]");
    const toastStack = document.querySelector("[data-toast-stack]");
    if (!badge || !toastStack || !("WebSocket" in window)) {
        return;
    }

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

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/`);

    socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "notification.created") {
            incrementBadge();
            showToast(message.notification);
            return;
        }

        if (message.type === "notification.unread_count") {
            setBadgeCount(message.unread_count);
        }
    });
})();

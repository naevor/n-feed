(() => {
    const forms = document.querySelectorAll("[data-follow-form]");
    if (!forms.length || !("fetch" in window)) {
        return;
    }

    const setFormPending = (form, pending) => {
        form.querySelectorAll("button").forEach((button) => {
            button.disabled = pending;
            button.setAttribute("aria-busy", pending ? "true" : "false");
        });
    };

    const updateFollowUi = (payload) => {
        const targetUserId = payload?.target_user_id;
        if (!targetUserId) {
            return;
        }

        document
            .querySelectorAll(`[data-follow-target-id="${targetUserId}"]`)
            .forEach((form) => {
                form.querySelectorAll("[data-follow-label]").forEach((element) => {
                    element.textContent = payload.follow_label || "Follow";
                });
            });

        document
            .querySelectorAll(`[data-profile-user-id="${targetUserId}"] [data-followers-count]`)
            .forEach((element) => {
                element.textContent = String(payload.followers_count);
            });

        document
            .querySelectorAll(
                `[data-profile-user-id="${payload.actor_user_id}"] [data-following-count]`
            )
            .forEach((element) => {
                element.textContent = String(payload.actor_following_count);
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

            updateFollowUi(await response.json());
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
})();

window.onload = function() {
    if (!document.body.classList.contains("login-page") && localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.classList.add("js");

    // Dark mode toggle with persisted preference across all pages.
    const body = document.getElementById("body") || document.body;
    const isLoginPage = body.classList.contains("login-page");
    const themeToggle = document.querySelector("[data-theme-toggle]");
    const savedTheme = window.localStorage.getItem("theme") || window.localStorage.getItem("theme_mode");

    function syncToggleLabel() {
        if (!themeToggle) {
            return;
        }
        themeToggle.textContent = body.classList.contains("dark-mode") ? "Light Mode" : "Dark Mode";
    }

    function applyTheme(theme) {
        if (theme === "dark") {
            body.classList.add("dark-mode");
        } else {
            body.classList.remove("dark-mode");
        }
        syncToggleLabel();
    }

    function toggleDarkMode() {
        body.classList.toggle("dark-mode");
        const isDark = body.classList.contains("dark-mode");
        window.localStorage.setItem("theme", isDark ? "dark" : "light");
        // Keep backward compatibility with old key.
        window.localStorage.setItem("theme_mode", isDark ? "dark" : "light");
        syncToggleLabel();
    }

    if (isLoginPage) {
        body.classList.remove("dark-mode");
    } else {
        applyTheme(savedTheme === "dark" ? "dark" : "light");
    }
    window.toggleDarkMode = toggleDarkMode;

    if (themeToggle) {
        themeToggle.addEventListener("click", toggleDarkMode);
    }

    // Confirm before logout action.
    document.querySelectorAll("[data-confirm-logout='true']").forEach((link) => {
        link.addEventListener("click", (event) => {
            const shouldLogout = window.confirm("Are you sure you want to logout?");
            if (!shouldLogout) {
                event.preventDefault();
            }
        });
    });

    // Auto-hide flash alerts.
    const alerts = document.querySelectorAll(".alert");
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach((alert) => {
                alert.style.transition = "opacity 0.4s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 420);
            });
        }, 4200);
    }

    // Ripple effect for interactive elements.
    const rippleTargets = document.querySelectorAll(".rippleable");
    rippleTargets.forEach((el) => {
        el.addEventListener("click", (event) => {
            const rect = el.getBoundingClientRect();
            const ripple = document.createElement("span");
            const isLoginButton = el.classList.contains("login-button");
            const sizeMultiplier = isLoginButton ? 0.72 : 0.55;
            const size = Math.max(rect.width, rect.height) * sizeMultiplier;

            ripple.className = "ripple";
            ripple.style.width = `${size}px`;
            ripple.style.height = `${size}px`;
            ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
            if (isLoginButton) {
                ripple.style.background = "rgba(241, 245, 249, 0.32)";
            }

            el.appendChild(ripple);
            setTimeout(() => ripple.remove(), isLoginButton ? 620 : 700);
        });
    });

    // Count-up animation for numeric badges and cards.
    const counters = document.querySelectorAll("[data-counter]");
    const counterObserver = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const targetEl = entry.target;
                const endValue = parseFloat(targetEl.getAttribute("data-counter") || "0");
                const suffix = targetEl.getAttribute("data-suffix") || "";
                const hasDecimal = !Number.isInteger(endValue);
                const duration = 1200;
                const start = performance.now();

                function animate(now) {
                    const progress = Math.min((now - start) / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = endValue * eased;

                    targetEl.textContent = hasDecimal ? `${current.toFixed(2)}${suffix}` : `${Math.round(current)}${suffix}`;

                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        targetEl.textContent = hasDecimal ? `${endValue.toFixed(2)}${suffix}` : `${Math.round(endValue)}${suffix}`;
                    }
                }

                requestAnimationFrame(animate);
                observer.unobserve(targetEl);
            });
        },
        { threshold: 0.45 }
    );

    counters.forEach((counter) => counterObserver.observe(counter));

    // Searchable custom department dropdown for Add Student page.
    const picker = document.querySelector("[data-department-picker]");
    if (picker) {
        const nativeSelect = picker.querySelector(".native-department-select");
        const trigger = picker.querySelector("[data-department-trigger]");
        const label = picker.querySelector("[data-department-label]");
        const panel = picker.querySelector("[data-department-panel]");
        const searchInput = picker.querySelector("[data-department-search]");
        const options = Array.from(picker.querySelectorAll("[data-department-option]"));
        const emptyState = picker.querySelector("[data-department-empty]");

        function setSelection(value) {
            const target = options.find((option) => option.dataset.value === value);
            if (!target) {
                return;
            }

            nativeSelect.value = value;
            label.textContent = value;

            options.forEach((option) => {
                const selected = option.dataset.value === value;
                option.classList.toggle("is-selected", selected);
                option.setAttribute("aria-selected", selected ? "true" : "false");
            });
        }

        function setOpenState(open) {
            picker.classList.toggle("open", open);
            trigger.setAttribute("aria-expanded", open ? "true" : "false");

            if (open) {
                searchInput.value = "";
                options.forEach((option) => {
                    option.hidden = false;
                });
                emptyState.hidden = true;
                searchInput.focus();
            }
        }

        // Initialize from existing selected option.
        setSelection(nativeSelect.value || options[0]?.dataset.value || "");

        trigger.addEventListener("click", () => {
            const open = picker.classList.contains("open");
            setOpenState(!open);
        });

        options.forEach((option) => {
            option.addEventListener("click", () => {
                setSelection(option.dataset.value || "");
                setOpenState(false);
            });
        });

        searchInput.addEventListener("input", () => {
            const query = searchInput.value.trim().toLowerCase();
            let visibleCount = 0;

            options.forEach((option) => {
                const match = option.textContent.toLowerCase().includes(query);
                option.hidden = !match;
                if (match) {
                    visibleCount += 1;
                }
            });

            emptyState.hidden = visibleCount > 0;
        });

        document.addEventListener("click", (event) => {
            if (!picker.contains(event.target)) {
                setOpenState(false);
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                setOpenState(false);
            }
        });
    }
});

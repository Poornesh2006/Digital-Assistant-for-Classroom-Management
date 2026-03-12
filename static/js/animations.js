document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("fade-in");

    const revealTargets = document.querySelectorAll(
        ".card, .stat-card, .student-card, .metric-item, .chart-shell, .profile-card, .table-shell"
    );

    revealTargets.forEach((element) => {
        element.classList.add("fade-section");
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries, revealObserver) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    entry.target.classList.add("visible");
                    revealObserver.unobserve(entry.target);
                });
            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -40px 0px",
            }
        );

        revealTargets.forEach((element) => observer.observe(element));
    } else {
        revealTargets.forEach((element) => element.classList.add("visible"));
    }
});

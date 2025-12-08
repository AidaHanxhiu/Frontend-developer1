document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signup-form");
    const messageEl = document.getElementById("signup-message");

    if (!form) {
        console.error("Signup form not found");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = document.getElementById("first-name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        messageEl.textContent = "Creating account...";
        messageEl.style.color = "black";

        try {
            const response = await fetch("/api/sign-up", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name,
                    email,
                    password,
                }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                messageEl.textContent = "Account created successfully!";
                messageEl.style.color = "green";
                setTimeout(() => {
                    window.location.href = "/log-in";
                }, 1000);
            } else {
                messageEl.textContent = data.message || "Signup failed";
                messageEl.style.color = "red";
            }
        } catch (error) {
            console.error(error);
            messageEl.textContent = "Error connecting to server";
            messageEl.style.color = "red";
        }
    });
});

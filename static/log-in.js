document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();  // Stop reload

        const email = document.querySelector("input[type='email']").value;
        const password = document.querySelector("input[type='password']").value;

        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        alert(result.message);
    });
});

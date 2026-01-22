// Run code only after the HTML page is fully loaded
document.addEventListener("DOMContentLoaded", () => {

  // Get the login form element
  const form = document.getElementById("login-form");

  // Get the element used to display login messages
  const messageEl = document.getElementById("login-message");

  // Check if the form exists
  if (!form) {
    console.error("Login form not found"); // Log error if form is missing
    return;                               // Stop script execution
  }

  // Listen for the form submission event
  form.addEventListener("submit", async (event) => {

    event.preventDefault();               // Prevent page reload on submit

    // Get user input values
    const email = document.getElementById("email").value;     // Email input
    const password = document.getElementById("password").value; // Password input

    // Show loading message
    messageEl.textContent = "Signing in...";
    messageEl.style.color = "black";

    try {
      // Send login request to backend API
      const response = await fetch("/api/login", {
        method: "POST",                   // HTTP POST method
        headers: {
          "Content-Type": "application/json", // Send JSON data
        },
        body: JSON.stringify({             // Convert login data to JSON
          email,
          password
        }),
      });

      // Convert server response to JSON
      const data = await response.json();

      // Check if login was successful
      if (response.ok) {

        // Display success message
        messageEl.textContent = data.message;
        messageEl.style.color = "green";

        // Save JWT token in browser storage
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
        }

        // Redirect user based on their role
        if (data.role === "admin") {
          window.location.href = "/admin";   // Admin dashboard
        } else {
          window.location.href = "/my-books"; // User dashboard
        }

      } else {
        // Handle invalid login credentials
        messageEl.textContent = data.message || "Login failed";
        messageEl.style.color = "red";
      }

    } catch (error) {
      // Handle network or server errors
      console.error(error);
      messageEl.textContent = "Error connecting to server";
      messageEl.style.color = "red";
    }
  });
});

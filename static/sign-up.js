// Run script after the page is fully loaded
document.addEventListener("DOMContentLoaded", () => {

    // Get signup form and message elements
    const form = document.getElementById("signup-form");
    const messageEl = document.getElementById("signup-message");
  
    // Check if the form exists
    if (!form) {
      console.error("Signup form not found"); // Log error
      return;                                // Stop execution
    }
  
    // Handle form submission
    form.addEventListener("submit", async (event) => {
  
      event.preventDefault();               // Prevent page reload
  
      // Get input values
      const name = document.getElementById("first-name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
  
      // Show loading message
      messageEl.textContent = "Creating account...";
      messageEl.style.color = "black";
  
      try {
        // Send signup request to the server
        const response = await fetch("/api/sign-up", {
          method: "POST",                   // Use POST method
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({             // Convert data to JSON
            name,
            email,
            password,
          }),
        });
  
        // Parse server response
        const data = await response.json();
  
        // If signup is successful
        if (response.ok && data.success) {
          messageEl.textContent = "Account created successfully!";
          messageEl.style.color = "green";
  
          // Redirect to login page after short delay
          setTimeout(() => {
            window.location.href = "/log-in";
          }, 1000);
  
        } else {
          // Handle signup failure
          messageEl.textContent = data.message || "Signup failed";
          messageEl.style.color = "red";
        }
  
      } catch (error) {
        // Handle network or server error
        console.error(error);
        messageEl.textContent = "Error connecting to server";
        messageEl.style.color = "red";
      }
    });
  });
  
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const messageEl = document.getElementById("login-message");
  
    if (!form) {
      console.error("Login form not found");
      return;
    }
  
    form.addEventListener("submit", async (event) => {
      event.preventDefault(); // stop page from reloading
  
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
  
      messageEl.textContent = "Signing in...";
      messageEl.style.color = "black";
  
      try {
        const response = await fetch("/api/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        });
  
        const data = await response.json();
  
        if (response.ok) {
          // successful login
          messageEl.textContent = data.message;
          messageEl.style.color = "green";
  
          // redirect based on role
          if (data.role === "admin") {
            window.location.href = "/admin";
          } else {
            window.location.href = "/my-books";
          }
        } else {
          // wrong email or password
          messageEl.textContent = data.message || "Login failed";
          messageEl.style.color = "red";
        }
      } catch (error) {
        console.error(error);
        messageEl.textContent = "Error connecting to server";
        messageEl.style.color = "red";
      }
    });
  });
  
document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const signupContainer = document.getElementById("signup-container");
  const accountButton = document.getElementById("account-button");
  const accountMenu = document.getElementById("account-menu");
  const openLoginButton = document.getElementById("open-login");
  const teacherAccount = document.getElementById("teacher-account");
  const teacherName = document.getElementById("teacher-name");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  let isTeacher = false;

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => `<li><span class="participant-email">${email}</span>${
                      isTeacher
                        ? `<button class="delete-btn" data-activity="${encodeURIComponent(name)}" data-email="${encodeURIComponent(email)}">Unregister</button>`
                        : ""
                    }</li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
      signupContainer.classList.toggle("hidden", !isTeacher);
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = decodeURIComponent(button.getAttribute("data-activity"));
    const email = decodeURIComponent(button.getAttribute("data-email"));

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  accountButton.addEventListener("click", () => {
    const isOpen = !accountMenu.classList.contains("hidden");
    accountMenu.classList.toggle("hidden", isOpen);
    accountButton.setAttribute("aria-expanded", String(!isOpen));
  });

  openLoginButton.addEventListener("click", () => {
    loginMessage.className = "hidden";
    loginForm.reset();
    loginDialog.showModal();
  });

  document.getElementById("cancel-login").addEventListener("click", () => {
    loginDialog.close();
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginMessage.className = "hidden";
    const credentials = {
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    };

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to log in.");
      }

      await updateAuthState();
      loginForm.reset();
      loginDialog.close();
      accountMenu.classList.add("hidden");
      accountButton.setAttribute("aria-expanded", "false");
      await fetchActivities();
    } catch (error) {
      loginMessage.textContent = error.message || "Unable to log in.";
      loginMessage.className = "error";
    }
  });

  document.getElementById("logout-button").addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      if (!response.ok) {
        throw new Error("Unable to log out.");
      }
      await updateAuthState();
      accountMenu.classList.add("hidden");
      accountButton.setAttribute("aria-expanded", "false");
      messageDiv.classList.add("hidden");
      await fetchActivities();
    } catch (error) {
      messageDiv.textContent = error.message || "Unable to log out.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
    }
  });

  async function updateAuthState() {
    const response = await fetch("/auth/status");
    if (!response.ok) {
      throw new Error("Unable to check teacher login status.");
    }
    const auth = await response.json();
    isTeacher = auth.authenticated;
    openLoginButton.classList.toggle("hidden", isTeacher);
    teacherAccount.classList.toggle("hidden", !isTeacher);
    teacherName.textContent = isTeacher ? `Logged in: ${auth.username}` : "";
    signupContainer.classList.toggle("hidden", !isTeacher);
  }

  async function initialize() {
    try {
      await updateAuthState();
      await fetchActivities();
    } catch (error) {
      activitiesList.textContent = "Unable to load the application. Please try again later.";
      console.error("Error initializing app:", error);
    }
  }

  initialize();
});

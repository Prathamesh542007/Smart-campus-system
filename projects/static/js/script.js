// =========================================================
// SMART CAMPUS COMPLAINT SYSTEM - JAVASCRIPT
// =========================================================

document.addEventListener("DOMContentLoaded", function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("show");
      if (backdrop) backdrop.classList.toggle("show");
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", function () {
      if (sidebar) sidebar.classList.remove("show");
      backdrop.classList.remove("show");
    });
  }

  // 2. Photo Upload Preview
  const photoInput = document.getElementById("photoInput");
  const photoPreview = document.getElementById("photoPreview");
  const previewContainer = document.getElementById("previewContainer");
  const fileNameDisplay = document.getElementById("fileNameDisplay");

  if (photoInput && photoPreview && previewContainer) {
    photoInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (file) {
        // Validate file type
        const validTypes = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"];
        if (!validTypes.includes(file.type)) {
          alert("Please select a valid image file (PNG, JPG, JPEG, GIF, WEBP).");
          photoInput.value = "";
          previewContainer.style.display = "none";
          if (fileNameDisplay) fileNameDisplay.textContent = "No file chosen";
          return;
        }

        // Validate max 16MB
        if (file.size > 16 * 1024 * 1024) {
          alert("Image file size must be under 16MB.");
          photoInput.value = "";
          previewContainer.style.display = "none";
          return;
        }

        const reader = new FileReader();
        reader.onload = function (event) {
          photoPreview.src = event.target.result;
          previewContainer.style.display = "block";
          if (fileNameDisplay) {
            fileNameDisplay.textContent = file.name;
          }
        };
        reader.readAsDataURL(file);
      } else {
        previewContainer.style.display = "none";
        if (fileNameDisplay) fileNameDisplay.textContent = "No file chosen";
      }
    });
  }

  // 3. Auto-dismiss Flash Alerts
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        alert.style.display = "none";
      }
    }, 5000);
  });

  // 4. Instant Table Quick Search Filter (for instant student table lookup)
  const clientSearchInput = document.getElementById("clientTableSearch");
  const targetTable = document.getElementById("complaintsTable");

  if (clientSearchInput && targetTable) {
    clientSearchInput.addEventListener("input", function () {
      const filter = this.value.toLowerCase().trim();
      const rows = targetTable.querySelectorAll("tbody tr");

      rows.forEach(function (row) {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }
});

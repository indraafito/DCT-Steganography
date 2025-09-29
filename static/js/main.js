function openInfoModal() {
  document.getElementById("infoModal").classList.remove("hidden");
  document.getElementById("infoModal").classList.add("flex");
  document.body.style.overflow = "hidden";
}

function closeInfoModal() {
  document.getElementById("infoModal").classList.add("hidden");
  document.getElementById("infoModal").classList.remove("flex");
  document.body.style.overflow = "auto";
}

function previewImage(input, previewId, containerId) {
  const preview = document.getElementById(previewId);
  const container = document.getElementById(containerId);
  const label = input.parentElement.previousElementSibling;

  if (input.files && input.files[0]) {
    const reader = new FileReader();

    reader.onload = function (e) {
      preview.src = e.target.result;
      container.classList.remove("hidden-preview");
      container.classList.add("show-preview");
      // Ubah teks label menjadi 'Ganti Gambar'
      label.innerHTML = `<i class="fas fa-exchange-alt mr-2"></i>Ganti Gambar`;
    };

    reader.readAsDataURL(input.files[0]);
  } else {
    container.classList.add("hidden-preview");
    container.classList.remove("show-preview");
    // Kembalikan teks label ke semula
    if (input.id === 'embed-image') {
      label.innerHTML = `<i class="fas fa-upload mr-2"></i>Pilih Gambar`;
    } else {
      label.innerHTML = `<i class="fas fa-search mr-2"></i>Pilih Gambar Steganografi`;
    }
  }
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
  document
    .getElementById("infoModal")
    .addEventListener("click", function (e) {
      if (e.target === this) {
        closeInfoModal();
      }
    });

  // Close modal with Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeInfoModal();
    }
  });
});
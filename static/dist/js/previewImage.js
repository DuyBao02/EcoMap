function previewImage(event) {
  const fileInput = document.getElementById('file-upload');
  const previewImg = document.getElementById('preview-img');
  const previewSection = document.getElementById('preview');
  const uploadBox = document.getElementById('upload-box');
  const reuploadSection = document.getElementById('reupload-section');

  if (fileInput.files && fileInput.files[0]) {
      const reader = new FileReader();
      reader.onload = function(e) {
          previewImg.src = e.target.result;  // Hiển thị hình ảnh xem trước
          previewSection.classList.remove('hidden');  // Hiển thị phần xem trước ảnh
          uploadBox.classList.add('hidden');  // Ẩn phần upload ảnh
          reuploadSection.classList.remove('hidden'); // Hiển thị phần re-upload ảnh
      };
      reader.readAsDataURL(fileInput.files[0]);  // Đọc file ảnh
  }
}

// Sự kiện cho nút "Upload lại ảnh"
document.getElementById('reupload-button').addEventListener('click', function() {
  document.getElementById('file-upload').click();
});

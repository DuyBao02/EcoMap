document.addEventListener("DOMContentLoaded", () => {
    const uploadBox = document.getElementById("map-upload-box");
    const preview = document.getElementById("map-preview");
    const previewImg = document.getElementById("map-preview-img");
    const reuploadSection = document.getElementById("map-reupload-section");
    const reuploadButton = document.getElementById("map-reupload-button");
    const fileInput = document.getElementById("map-file-upload");

    // Xử lý sự kiện dán (paste)
    uploadBox.addEventListener("paste", (event) => {
        const items = event.clipboardData.items;
        let foundImage = false;

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.type.startsWith("image/")) {
            foundImage = true;
            const file = item.getAsFile();

            // Tạo tên file dựa trên timestamp
            const timestamp = Date.now();
            const fileName = `clipboard_image_${timestamp}.png`;

            // Tạo File mới với tên tùy chỉnh
            const renamedFile = new File([file], fileName, { type: file.type });

            const reader = new FileReader();

            reader.onload = (e) => {
                // Hiển thị ảnh xem trước
                showPreview(e.target.result);

                // Gắn file vào fileInput
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(renamedFile);
                fileInput.files = dataTransfer.files; // Gán file vào fileInput
            };

            reader.readAsDataURL(file);
            break; // Chỉ xử lý một ảnh đầu tiên được dán
            }
        }

        if (!foundImage) {
            alert(alertSomethingWrong);
        }
    });

    // Xử lý sự kiện chọn file qua input
    fileInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        let foundImage = false;

        if (file) {
            // Kiểm tra nếu file là ảnh (bắt đầu bằng "image/")
            if (file.type.startsWith("image/")) {
                foundImage = true;
                const reader = new FileReader();

                reader.onload = (e) => {
                    // Hiển thị ảnh xem trước
                    showPreview(e.target.result);
                };

                reader.readAsDataURL(file);
            } else {
                fileInput.value = ""; // Reset input file nếu không phải ảnh
            }
        }
        if (!foundImage) {
            alert(alertSomethingWrong);
        }
    });

    // Hiển thị ảnh xem trước
    function showPreview(imageSrc) {
        previewImg.src = imageSrc;
        preview.classList.remove("hidden");
        reuploadSection.classList.remove("hidden");
        uploadBox.classList.add("hidden");
    }

    // Xử lý nút tải lại ảnh
    reuploadButton.addEventListener("click", () => {
        preview.classList.add("hidden");
        reuploadSection.classList.add("hidden");
        uploadBox.classList.remove("hidden");
        previewImg.src = "";
        fileInput.value = ""; // Reset input file
    });
});

// Sự kiện cho nút "Upload lại ảnh"
document.getElementById('map-reupload-button').addEventListener('click', function() {
    document.getElementById('map-file-upload').click();
});
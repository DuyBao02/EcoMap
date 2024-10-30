from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_babel import Babel, _, lazy_gettext as _l, gettext
import os, glob, pytz, sys, zipfile, shutil
from datetime import datetime

app = Flask(__name__)

#------------------------------------------#####---------------------------------------#

#Language config
babel = Babel(app)
app.config['SECRET_KEY'] = '604ab4ed4ab64b1b19449696'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = './translations'

#--------------------------------------------------------------------------------------

# Change Language Functions
def get_locale():
    # Kiểm tra nếu người dùng đã chọn ngôn ngữ từ query string
    if 'lang' in request.args:
        lang = request.args.get('lang')
        if lang in ['en', 'vi', 'de']:
            session['lang'] = lang  # Lưu vào session
            return lang
    # Nếu không có ngôn ngữ trong session, trả về ngôn ngữ mặc định là 'en'
    elif 'lang' in session:
        return session['lang']
    # Nếu không có ngôn ngữ trong session, trả về ngôn ngữ mặc định là 'en'
    return 'en'

babel = Babel(app, locale_selector=get_locale)

@app.route('/setlang')
def setlang():
    lang = request.args.get('lang', 'en')
    session['lang'] = lang
    return redirect(request.referrer)

@app.context_processor
def inject_babel():
    return dict(_=gettext)

@app.context_processor
def inject_locale():
    # This makes the function available directly, allowing you to call it in the template
    return {'get_locale': get_locale}

#------------------------------------------#####---------------------------------------#

#Folder image config
UPLOAD_FOLDER = 'static/uploadsImg/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

MAX_IMAGES = 20  # Giới hạn số ảnh

vi_tz = pytz.timezone('Asia/Ho_Chi_Minh') # Múi giờ Việt Nam (UTC+7)

#--------------------------------------------------------------------------------------

def get_sorted_images():
    # Lấy danh sách tất cả file hình ảnh trong thư mục uploads và sắp xếp theo thời gian chỉnh sửa
    image_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
    
    # Sắp xếp ảnh theo thời gian chỉnh sửa (modified time) nhưng sử dụng múi giờ Việt Nam
    image_files.sort(key=lambda x: datetime.fromtimestamp(os.path.getmtime(x), vi_tz), reverse=True)  # Sắp xếp theo thời gian chỉnh sửa giảm dần
    return image_files

def cleanup_old_images():
    # Nếu có quá MAX_IMAGES ảnh, xóa các ảnh cũ nhất
    image_files = get_sorted_images()
    if len(image_files) > MAX_IMAGES:
        for image_file in image_files[MAX_IMAGES:]:
            os.remove(image_file)  # Xóa các file cũ ngoài giới hạn

# Hàm này lấy tên thư mục dựa trên tên ảnh đầu vào
def get_folder_name(image_path):
    return os.path.splitext(os.path.basename(image_path))[0]

# Xóa các folder cũ khi vượt quá 10
def cleanup_old_folders(directory, max_folders=10):
    folders = [os.path.join(directory, d) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    if len(folders) > max_folders:
        # Sắp xếp các thư mục theo thời gian tạo
        folders.sort(key=os.path.getctime)
        # Xóa các thư mục cũ nhất cho đến khi số lượng <= max_folders
        for folder in folders[:-max_folders]:
            shutil.rmtree(folder)
            print(f"Đã xóa thư mục cũ: {folder}")

#--------------------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():
    imgsteps = [
        {'is_completed': False},  # Step 1 chưa hoàn thành
        {'is_completed': False},  # Step 2 chưa hoàn thành
    ]

    if request.method == "POST":
        file = request.files.get('file-upload')  # Lấy file từ form

        if file:
            # Lưu file vào thư mục uploads
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            # Xóa các ảnh cũ nếu quá số lượng
            cleanup_old_images()

            # Đánh dấu bước 1 đã hoàn thành
            imgsteps[0]['is_completed'] = True

            # Lấy hình ảnh mới nhất
            image_files = get_sorted_images()
            latest_image = image_files[0] if image_files else None

            # Lưu vào session
            session['latest_image'] = latest_image

            # Chuyển tiếp đến /ImageWasDetected với các biến cần thiết
            return redirect(url_for('ImageWasDetected'))

    return render_template("imgDetect/imgInput.html", imgsteps=imgsteps, latest_image=None, current_locale=get_locale())

#--------------------------------------------------------------------------------------

# Thêm đường dẫn của thư mục model vào sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'model'))

try:
    from detect_mask import run_detection  # Import hàm từ detect-mask.py
except ModuleNotFoundError:
    print("Lỗi: Không tìm thấy module 'detect_mask'. Hãy chắc chắn file detect-mask.py nằm trong thư mục 'model'.")

#--------------------------------------------------------------------------------------

@app.route("/download_zip")
def download_zip():
    # Lấy từ session
    latest_image = session.get('latest_image')
    
    if not latest_image:
        return "No image found"

    # Đường dẫn thư mục lưu ảnh đã detect
    folder_name = get_folder_name(latest_image)
    folder_path = os.path.join('static/imgDetected', folder_name)
    
    # Tên tập tin .zip
    zip_filename = f"{folder_name}.zip"
    
    # Tạo tập tin .zip
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder_path))

    # Gửi tập tin .zip cho client
    return send_file(zip_filename, as_attachment=True)

#--------------------------------------------------------------------------------------

@app.route("/imagewasdetected", methods=["GET"])
def ImageWasDetected():
    latest_image = session.get('latest_image')
    if not latest_image:
        return "<script>alert('Image cannot found'); window.location.href='/';</script>"
    
    input_image_path = latest_image
    output_dir = os.path.join('static/imgDetected')
    cleanup_old_folders(output_dir)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    save_dir, detected = run_detection(input_image_path, output_dir)
    if not detected:
        return "<script>alert('No masks detected, try again!'); window.location.href='/';</script>"
    
    detected_images = [os.path.join(save_dir, img).replace('\\', '/') for img in os.listdir(save_dir) if img.endswith('.png')]
    imgsteps = [{'is_completed': True}, {'is_completed': True}]
    
    return render_template("imgDetect/ImageWasDetected.html", detected_images=detected_images, imgsteps=imgsteps)

#------------------------------------------#####---------------------------------------#

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/map")
def map():
    return render_template('mapDetect/map.html')

if __name__ == '__main__':
	app.run(debug=True, port=9999)

# @app.route("/map")
# def map():
#     # Default map URL for Can Tho
#     map_url = "https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d3601.435709505139!2d105.77109809289283!3d10.030144987331482!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e1!3m2!1svi!2s!4v1728895692688!5m2!1svi!2s"
#     return render_template('map.html', map_url=map_url)

# @app.route('/search-location', methods=['POST'])
# def search_location():
#     location = request.form.get('location')
#     # Tạo URL Google Maps tìm kiếm từ địa chỉ người dùng nhập
#     google_maps_url = f"https://www.google.com/maps/search/?q={location}"
    
#     # Chuyển hướng đến trang có bản đồ Google Maps đã nhúng
#     return redirect(url_for('map_view', url=google_maps_url))

# @app.route('/map-view')
# def map_view():
#     url = request.args.get('url')
#     return render_template('map.html', url=url)



from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, send_from_directory
from flask_babel import Babel, _, lazy_gettext as _l, gettext
import os, glob, pytz, sys, zipfile, shutil, tempfile
from datetime import datetime

app = Flask(__name__)

# Định nghĩa filter 'zip'
def jinja2_zip(*args, **kwargs):
    return zip(*args, **kwargs)

# Đăng ký filter vào Jinja2 environment
app.jinja_env.filters['zip'] = jinja2_zip

#------------------------------------------#####---------------------------------------#

#Language config
babel = Babel(app)
app.config['SECRET_KEY'] = '604ab4ed4ab64b1b19449696'
app.config['BABEL_DEFAULT_LOCALE'] = 'vi'
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
    # Nếu không có ngôn ngữ trong session, trả về ngôn ngữ mặc định là 'vi'
    return 'vi'

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

MAX_IMAGES = 15  # Giới hạn số ảnh

vi_tz = pytz.timezone('Asia/Ho_Chi_Minh') # Múi giờ Việt Nam (UTC+7)

#--------------------------------------------------------------------------------------

def ensure_folder_exists(folder):
    # Đảm bảo rằng thư mục tồn tại. Nếu không, tạo mới.
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_sorted_images(upload_folder):
    # Lấy danh sách tất cả file trong thư mục
    image_files = glob.glob(os.path.join(upload_folder, '*'))
    
    # Sắp xếp theo thời gian chỉnh sửa (giảm dần) sử dụng múi giờ Việt Nam
    image_files.sort(key=lambda x: datetime.fromtimestamp(os.path.getmtime(x), vi_tz), reverse=True)
    return image_files

def cleanup_old_images(upload_folder):
    # Lấy danh sách các file đã sắp xếp
    image_files = get_sorted_images(upload_folder)
    
    # Nếu số file vượt quá `MAX_IMAGES`, xóa file cũ nhất
    if len(image_files) > MAX_IMAGES:
        for image_file in image_files[MAX_IMAGES:]:
            os.remove(image_file)  # Xóa file


# Hàm này lấy tên thư mục dựa trên tên ảnh đầu vào
def get_folder_name(image_path):
    return os.path.splitext(os.path.basename(image_path))[0]

# Xóa các folder cũ khi vượt quá 15
def cleanup_old_folders(directory, max_folders=15):
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
    mapsteps = [
        {'is_completed': False},  # Step 1 chưa hoàn thành
        {'is_completed': False},  # Step 2 chưa hoàn thành
    ]

    # Cấu hình thư mục lưu ảnh
    UPLOAD_FOLDER = "static/map/uploadsMap"
    ZIP_FOLDER = "static/map/mapDetected"

    if request.method == "POST":
        file = request.files.get('map-file-upload')  # Lấy file từ form

        if file:
            # Lưu file vào thư mục uploads
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)

            # Xóa các ảnh cũ nếu quá số lượng
            cleanup_old_images(UPLOAD_FOLDER)

            # Đánh dấu bước 1 đã hoàn thành
            mapsteps[0]['is_completed'] = True

            # Lấy hình ảnh mới nhất
            image_files = get_sorted_images(UPLOAD_FOLDER)
            map_latest_image = image_files[0] if image_files else None

            # Lưu vào session
            session['map_latest_image'] = map_latest_image
            session['ZIP_FOLDER'] = ZIP_FOLDER

            # Chuyển tiếp đến /mapwasdetected với các biến cần thiết
            return redirect(url_for('MapWasDetected'))

    # Lưu trạng thái bước vào session
    session['mapsteps'] = mapsteps

    # Cấu hình Google Maps
    api_key = ""
    map_url = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.030145,105.771098&zoom=12&maptype=satellite"

    alert_upload_image = gettext('Please upload an image before submitting.')
    confirm_upload_image = gettext('Do you want to upload the image?')
    alert_something_wrong = gettext('Something was wrong.')

    return render_template(
        "mapDetect/mapInput.html",
        map_url=map_url,
        mapsteps=mapsteps,
        alert_upload_image=alert_upload_image, 
        confirm_upload_image=confirm_upload_image, 
        alert_something_wrong=alert_something_wrong, 
        map_latest_image=None,
        ZIP_FOLDER=None,
        current_locale=get_locale()
    )

@app.route('/search-location', methods=['POST'])
def search_location():
    location = request.form.get('location')
    api_key = ""
    # Tạo URL Google Maps tìm kiếm từ địa chỉ người dùng nhập
    google_maps_url = f"https://www.google.com/maps/embed/v1/search?key={api_key}&q={location}&zoom=12&maptype=satellite"

    # Chuyển hướng đến trang có bản đồ Google Maps đã nhúng
    return redirect(url_for('map_view', url=google_maps_url, search="true"))

@app.route('/map-view')
def map_view():
    mapsteps = session.get('mapsteps')
    url = request.args.get('url')
    return render_template("mapDetect/mapInput.html", map_url=url, mapsteps=mapsteps)

@app.route("/mapwasdetected", methods=["GET"])
def MapWasDetected():
    map_latest_image = session.get('map_latest_image')
    if not map_latest_image:
        message = gettext('Image cannot be found')
        return render_template('redirect_with_alert.html', alert_message=message, redirect_url='/')
    
    input_image_path = map_latest_image
    output_dir = os.path.join('static/map/mapDetected')
    cleanup_old_folders(output_dir)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    save_dir, detected, percentages, areas, total_area, total_percentage, original_area = run_detection(input_image_path, output_dir)
    
    if not detected:
        message = gettext('No masks detected, try again!')
        return render_template('redirect_with_alert.html', alert_message=message, redirect_url='/')
    
    detected_images = [os.path.join(save_dir, img).replace('\\', '/') for img in os.listdir(save_dir) if img.endswith('.png')]
    
    # Tách ảnh gốc và các ảnh polygon
    original_image = detected_images[0] if detected_images else None
    polygon_images = detected_images[1:]  # Các ảnh polygon sau ảnh gốc

    # Đảm bảo tỷ lệ phần trăm chỉ áp dụng cho các polygon
    polygon_data = list(zip(polygon_images, percentages, areas))  # Kết hợp ảnh, tỷ lệ phần trăm và diện tích

    mapsteps = [{'is_completed': True}, {'is_completed': True}]
    
    return render_template("mapDetect/MapWasDetected.html",
                            detected_images=detected_images,
                            num_detected_images=len(polygon_images),  # Số lượng polygon
                            original_image=original_image,  # Ảnh gốc
                            polygon_data=polygon_data,  # Danh sách tuple (ảnh polygon, %)
                            total_area=total_area,
                            total_percentage=total_percentage,
                            original_area=original_area,
                            mapsteps=mapsteps,
                            current_locale=get_locale())

#------------------------------------------#####---------------------------------------#

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
    map_latest_image = session.get('map_latest_image')
    ZIP_FOLDER = session.get('ZIP_FOLDER')

    if not map_latest_image:
        return "No image found"

    # Đường dẫn thư mục lưu ảnh đã detect
    folder_name = get_folder_name(map_latest_image)
    folder_path = os.path.join(ZIP_FOLDER, folder_name)

    # Kiểm tra thư mục tồn tại
    if not os.path.exists(folder_path):
        return f"Folder {folder_path} does not exist"

    # Tạo file ZIP tạm thời
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

        temp_zip_path = temp_zip.name  # Lưu đường dẫn file ZIP tạm thời

    # Gửi file ZIP cho client
    response = send_file(temp_zip_path, as_attachment=True)

    # Xóa file ZIP tạm thời sau khi gửi
    @response.call_on_close
    def cleanup_temp_file():
        try:
            os.remove(temp_zip_path)
        except OSError as e:
            print(f"Error deleting temporary file: {e}")

    return response
#------------------------------------------#####---------------------------------------#

from chatbot.germini import RAG

# Tạo một đối tượng RAG 
excel_file = "chatbot/Don_vi_Can_Tho.xlsx"
sheet_name = "DonviCanTho"
llmApiKey = ""
rag = RAG(excel_file, sheet_name, llmApiKey)

@app.route("/pictures/<path:filename>")
def serve_pictures(filename):
    return send_from_directory("chatbot/pictures", filename)

@app.route("/chatwithbot")
def chatwithbot():
    return render_template("otherpages/qawb.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "No message received."})
    
    source_information = rag.enhance_prompt(user_message)
    combined_information = f"Hãy trở thành chuyên gia thông tin về các đơn vị hành chính ở Cần Thơ. \
        Câu hỏi của người dùng: {user_message}\nTrả lời câu hỏi dựa vào các thông tin dưới đây: {source_information}. \
        Nếu {user_message} liên quan đến mô tả, tóm tắt sơ lược hoặc lấy thông tin cơ bản thì lấy cột mo_ta ứng với đơn vị hành chính tìm được để trả lời.\
        Nếu {user_message} liên quan đến diện tích thì đơn vị là (km\u00B2), \
            {user_message} liên quan đến mật độ dân số thì đơn vị là người/km\u00B2, \
            {user_message} liên quan đến dân số thì đơn vị là người và lấy số liệu từ mật độ dân số và diện tích để ra kết quả, \
            kết quả này chỉ là khoảng ước chừng chứ không chắc chắn 100%. \
        Nếu không có thông tin thì trả lời: 'Thông tin đang được cập nhật, vui lòng xem chi tiết tại: [Trang thông tin Cần Thơ]', \
            không được đưa ra thông tin sai"
    
    bot_response = rag.generate_content(combined_information)
    response_text = bot_response.text

    get_knowledge = rag.vector_search(user_message)
    first_result = get_knowledge[0] if get_knowledge else None

    # Kiểm tra câu hỏi của người dùng có liên quan đến địa điểm hay không
    location_keywords = [
        "địa danh"
        "địa điểm",
        "thú vị",
        "đặc sắc",
        "nổi bật",
        "nơi nổi bật",
        "tham quan",
        "điểm tham quan",
        "điểm đến",
        "du lịch",
        "chơi",
        "tham quan du lịch",
        "điểm du lịch",
        "cảnh đẹp",
        "điểm đến lý tưởng",
        "danh lam thắng cảnh",
        "danh thắng",
        "địa điểm tham quan",
        "có gì hot",
        "vui"
        "độc đáo",
        "hấp dẫn",
        "đặc biệt",
        "thơ mộng",
        "vẻ vang",
        "hùng vĩ"
    ]

    is_location_query = any(keyword in user_message.lower() for keyword in location_keywords)

    locations_with_images = []
    if is_location_query and first_result and first_result["dia_diem_hinh_anh"]:
        valid_entries = [
                            item for item in first_result["dia_diem_hinh_anh"]
                            if item["dia_diem"].lower() != 'nan' and item["hinh_anh"].lower() != 'nan'
                        ]
        if valid_entries:
            locations_with_images = [{"dia_diem": [item["dia_diem"] for item in valid_entries], 
                                      "hinh_anh": [item["hinh_anh"] for item in valid_entries]}]

    return jsonify({"response": response_text, "locations": locations_with_images})

#--------------------------------------------------------------------------------------#
import speech_recognition as sr
import pyttsx3

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "No text provided."})

    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50) # Tốc độ nói
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    
    output_file = 'chatbot/output.mp3'
    engine.save_to_file(text, output_file)
    engine.runAndWait()
    
    return send_file(output_file, as_attachment=True)

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    recognizer = sr.Recognizer()
    audio_data = request.files['audio_data']
    with sr.AudioFile(audio_data) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language='vi-VN')
            return jsonify({'text': text})
        except sr.UnknownValueError:
            return jsonify({'text': 'Không nhận diện được âm thanh.'})
        except sr.RequestError as e:
            return jsonify({'text': f'Error: {e}'})
    return jsonify({'text': 'Lỗi xử lý âm thanh.'})

#------------------------------------------#####---------------------------------------#

@app.route("/contacts")
def contacts():
    return render_template("otherpages/contacts.html")

@app.errorhandler(404)
def page_not_found(e): 
    return render_template('404.html'), 404

if __name__ == '__main__':
	app.run(debug=True)

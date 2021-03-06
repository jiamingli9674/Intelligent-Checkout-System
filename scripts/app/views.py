import pickle
from flask_admin.contrib import sqla
from flask_security import current_user
from flask import  url_for, redirect, request, abort, Response, flash
from flask_admin import BaseView, expose
from app import db
from app.database import RegisteredUser, Product
from flask.templating import render_template
from utility.user_info_form import UserInfoForm
from utility.post_form import PostForm
from utility.video_camera import VideoCamera
from const.consts import FACE_ID_ENCODING_SUCESS
from werkzeug.utils import secure_filename
import os


import cv2

    
# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


    # can_edit = True
    edit_modal = True
    create_modal = True    
    can_export = True
    can_view_details = True
    details_modal = True

class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list

class ProductView(MyModelView):
    column_editable_list = ['product_name', 'product_unit_price', 'product_code', 'product_discount']
    column_searchable_list = column_editable_list
   
    column_filters = column_editable_list
    
class RegisteredUserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name', 'balance']
    column_exclude_list = ['face_encoding']
    column_details_exclude_list = column_exclude_list
    column_searchable_list = column_editable_list
    column_filters = column_editable_list


class CheckoutView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/checkout.html')

    def gen_check_identity_frame(self, camera):
        while True:
            frame = camera.check_identity()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    @expose('/check_identity')
    def check_identity(self):
        return Response(self.gen_check_identity_frame(VideoCamera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame') 

user_email = None
encoded_frame = None

class UserRegistrationView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = UserInfoForm(request.form)
        if request.method == 'POST' and form.validate():
            global encoded_frame
            encoded_frame = None
            user = RegisteredUser()
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            global user_email
            user_email = form.email.data
            db.session.add(user)
            db.session.commit()
            return self.render('admin/face_encoding.html', frame = None, form = PostForm())

        return self.render('admin/user_registration.html', form=UserInfoForm())
    
    def gen_face_encoding_frame(self, camera):
        while True:
            status ,face_encoding, frame_byte = camera.encode_face()
            yield (status, face_encoding, b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_byte + b'\r\n\r\n')                     
    
    def get_frame(self, camera):
        while True:
            frame_byte = camera.read_frame()
            yield  b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_byte + b'\r\n\r\n' 
            
    @expose('/gen_frame')
    def gen_frame(self):
        return Response(self.get_frame(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')   
    
    @expose('/encoded_face')
    def encoded_face(self):
        return Response(encoded_frame,
                    mimetype='multipart/x-mixed-replace; boundary=frame')   
        
    @expose('/encode_face', methods=["POST", "GET"])
    def encode_face(self):
        global encoded_frame
        if not encoded_frame:
            status, face_encoding, frame_bytes = next(self.gen_face_encoding_frame(VideoCamera()))
            encoded_frame = frame_bytes
            if status == FACE_ID_ENCODING_SUCESS:
                global encode_success
                encode_success = True
                global user_email
                user = db.session.query(RegisteredUser).filter(RegisteredUser.email == user_email).first()
                user.face_encoding = pickle.dumps(face_encoding)
                db.session.add(user)
                db.session.commit()
                return self.render('admin/face_encoding.html', frame = frame_bytes, form = PostForm())

import tensorflow as tf
from utility.mask_rcnn import MaskRCNN
g = tf.Graph()
with g.as_default():
    print("Loading model")
    model = MaskRCNN()

class ObjectDetectionView(BaseView):
    
    def allowed_file(self, filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg'}
           
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        global model, g
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and self.allowed_file(file.filename):
                
                filename = 'img.jpg'
                file.save(os.path.join(os.path.join(os.path.dirname(__file__), "static", "img"), filename))
                img = cv2.imread(os.path.join(os.path.join(os.path.dirname(__file__), "static", "img"), filename))
                with g.as_default():
                    img = model.detect(img)
                cv2.imwrite(os.path.join(os.path.join(os.path.dirname(__file__), "static", "img"), "img_res.png"), img)
                return self.render('admin/object_detection.html', img = True)
            
        return self.render('admin/object_detection.html', img = False)
    
    
    
        
    
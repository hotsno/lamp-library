from flask import Blueprint, jsonify, request, Response
from datetime import datetime
import os
import zipfile
import re
from file_watcher import get_library_data

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def api_home():
    """API home endpoint"""
    return jsonify({
        'message': 'Welcome to the API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/library', methods=['GET'])
def get_library():
    """Get the library with detailed information from JSONDict"""
    library_data = get_library_data()
    if library_data is None:
        return jsonify({'error': 'Library data not available'}), 500
    
    # Return library data with manga information
    return jsonify({
        'library': library_data,
        'total_manga': len(library_data),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@api_bp.route('/chapters/<string:manga_id>', methods=['GET'])
def get_chapters(manga_id):
    """Get a specific manga's chapters"""
    manga_path = os.path.join(os.environ.get('MANGA_PATH'), manga_id)
    if not os.path.isdir(manga_path):
        return jsonify({'error': 'Manga not found'}), 404

    chapter_files = sorted([name for name in os.listdir(manga_path) if name.endswith('.cbz')])
    chapters = []
    for chapter_file in chapter_files:
        volume_match = re.search(r'v(\d+)', chapter_file)
        chapter_match = re.search(r'c(\d+(?:\.\d+)?)', chapter_file)
        
        volume = None
        if volume_match:
            volume = int(volume_match.group(1))
        
        chapter = None
        if chapter_match:
            chapter_str = chapter_match.group(1)
            chapter_num = float(chapter_str)
            chapter = str(int(chapter_num)) if chapter_num.is_integer() else str(chapter_num)
        
        chapters.append({
            'chapter': chapter,
            'volume': volume
        })

    return jsonify({'chapters': chapters}), 200

@api_bp.route('/page/<string:manga_id>/<int:chapter_id>/<int:page_number>', methods=['GET'])
def get_page(manga_id, chapter_id, page_number):
    """Get a specific page from a CBZ chapter file"""
    manga_path = os.path.join(os.environ.get('MANGA_PATH'), manga_id)
    if not os.path.isdir(manga_path):
        return jsonify({'error': 'Manga not found'}), 404

    chapters = sorted([name for name in os.listdir(manga_path) if name.endswith('.cbz')])
    
    if chapter_id < 0 or chapter_id >= len(chapters):
        return jsonify({'error': 'Chapter not found'}), 404
    
    chapter_file = chapters[chapter_id]
    chapter_path = os.path.join(manga_path, chapter_file)
    
    try:
        with zipfile.ZipFile(chapter_path, 'r') as cbz_file:
            file_list = sorted(cbz_file.namelist())
            image_files = [f for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]
            if page_number < 0 or page_number >= len(image_files):
                return jsonify({'error': 'Page not found'}), 404
            
            image_file = image_files[page_number]
            image_data = cbz_file.read(image_file)
            file_ext = image_file.lower().split('.')[-1]
            content_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'webp': 'image/webp'
            }
            content_type = content_type_map.get(file_ext, 'image/jpeg')
            return Response(image_data, mimetype=content_type)
            
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid CBZ file'}), 400
    except Exception as e:
        return jsonify({'error': f'Error reading CBZ file: {str(e)}'}), 500

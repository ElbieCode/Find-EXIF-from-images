import os
import requests
from PIL import Image
from PIL.ExifTags import TAGS
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import argparse


def extract_exif_metadata(image_path, gps_only):
    try:
        exif_data = Image.open(image_path)._getexif()
        if exif_data:
            exif_metadata = {}
            for tag, value in exif_data.items():
                if gps_only:
                    if TAGS.get(tag) == 'GPSInfo':
                        exif_metadata[TAGS.get(tag)] = value
                        break
                else:
                    tag_name = TAGS.get(tag, tag)
                    exif_metadata[tag_name] = value
            return exif_metadata
    except Exception as e:
        print(f"Loi trich xuat sieu du lieu EXIF tu anh {image_path}: {e}")
    return None


def gps_info_to_google_maps_link(gps_info):
    if gps_info:
        lat = gps_info.get(2)
        lon = gps_info.get(4)
        if lat is not None and lon is not None:
            lat_decimal = lat[0] + lat[1]/60 + lat[2]/3600
            lon_decimal = lon[0] + lon[1]/ 60 + lon[2]/3600

            return f"https://www.google.com/maps?q={lat_decimal:.7f},{lon_decimal:.7f}"
    return None


def save_metadata_to_text(metadata, output_folder, gps_only):
    if gps_only:
        for image_path, meta in metadata.items():
            for tag, value in meta.items():
                google_maps_link = gps_info_to_google_maps_link(value)
                if google_maps_link:
                    print(f"Link Google Maps cho anh {os.path.basename(image_path)}: {google_maps_link}")
                else:
                    print(f"Khong co du lieu GPS cu the cho {os.path.basename(image_path)}")
    else:
        for image_path, meta in metadata.items():
            filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
            output_file = os.path.join(output_folder, filename)
            with open(output_file, 'w') as f:
                for tag, value in meta.items():
                    f.write(f'{tag}: {value}\n')
            print(f"Luu EXIF cua anh {os.path.basename(image_path)} thanh cong!")


def download_images_from_url(url, output_folder, gps_only):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tags = soup.find_all('img')
        metadata = {}
        for img_tag in img_tags:
            img_url = img_tag.get('src')
            if img_url:
                img_url = urljoin(url, img_url)
                img_name = os.path.basename(urlparse(img_url).path)
                img_path = os.path.join(output_folder, img_name)
                if img_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_data = requests.get(img_url).content
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    exif_metadata = extract_exif_metadata(img_path, gps_only)
                    if exif_metadata:
                        print(f"Anh: {img_name} da luu ve thanh cong.")
                        metadata[img_path] = exif_metadata
                    else:
                        os.remove(img_path)
                        print(f"Da xoa anh: {img_name} vi khong co EXIF metadata.")
                else:
                    print(f"Khong the tai hinh anh {img_name}")
        print("--------------------------------------------------------------------")
        save_metadata_to_text(metadata, output_folder, gps_only)
    else:
        print("Ket noi voi trang web that bai!")


def extract_exif_from_folder(folder_path, output_folder, gps_only):
    metadata = {}
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder_path, filename)
            exif_metadata = extract_exif_metadata(image_path, gps_only)
            if exif_metadata:
                metadata[image_path] = exif_metadata
    save_metadata_to_text(metadata, output_folder, gps_only)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triet xuat thong tin EXIF tu tat ca anh"
                                                 " trong folder hoac tu anh trong URL")
    parser.add_argument("output_folder", help="Duong dan den thu muc dau ra.")
    parser.add_argument("--folder", help="Duong dan cua thu muc dau vao.")
    parser.add_argument("--url", help="URL cua trang web chua hinh anh.")
    parser.add_argument("--gps", default=False, action="store_true",
                        help="Chi triet xuat thong tin GPS")

    args = parser.parse_args()

    if not os.path.exists(args.output_folder):
        print(f"Thu muc {args.output_folder} khong ton tai! Dang tao moi")
        os.makedirs(args.output_folder)

    if args.folder:
        if os.path.exists(args.folder):
            extract_exif_from_folder(args.folder,args.output_folder,args.gps)
        else:
            print(f"Thu muc {args.folder} khong ton tai!")

    if args.url:
        download_images_from_url(args.url, args.output_folder, args.gps)

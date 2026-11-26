# ttpfoods.vn

Website giới thiệu Công ty TNHH Thực phẩm TTP (TTP Foods).

## Cấu trúc

```
src/
  layouts/base.html      khung chung: head, header + menu, footer
  pages/*.html           mỗi trang một file (home, about, leadership, products, services, contact, 404)
  partials/*.html        các khối nội dung dùng chung
  assets/                css, js, fonts (Montserrat tự lưu), img
  static/                file đặt ở gốc website (CNAME, favicon.ico, site.webmanifest)
  legacy-products.json   địa chỉ cũ của website trước -> trang mới
build.py                 công cụ dựng trang (Python 3.9+, Jinja2, Pillow)
docs/                    website đã dựng – GitHub Pages phục vụ thư mục này (không sửa tay)
```

Nội dung song ngữ viết **một lần** trong template:
`<span class="l-vi">Tiếng Việt</span><span class="l-en">English</span>` hoặc `{{ t('Tiếng Việt', 'English') }}`.
Khi dựng, mỗi trang được xuất 2 lần: tiếng Việt tại `/…`, tiếng Anh tại `/en/…`; phần ngôn ngữ kia bị loại bỏ.

## Làm việc

```bash
python3 build.py --check                              # dựng + kiểm tra liên kết, ảnh, tiêu đề
python3 -m http.server 8090 --directory docs          # xem trước tại http://localhost:8090
```

Thêm trang mới: tạo `src/pages/<ten>.html`, khai báo trong `PAGES` (và `NAV` nếu cần) ở `build.py`.

## Phát hành

Nhánh `main` = website đang chạy. Phát triển trên nhánh khác, duyệt xong mới gộp vào `main`,
gắn nhãn phiên bản (`v2.0`, `v2.1`…). GitHub Pages: *Settings → Pages → Deploy from branch → main / docs*.

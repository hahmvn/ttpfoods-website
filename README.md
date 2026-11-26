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
python3 build.py --check                              # dựng + kiểm tra liên kết, ảnh, tiêu đề, nội dung bắt buộc
python3 tools/qa.py                                   # kiểm tra trước phát hành: HTML, id, nhãn form, tiêu đề, tương phản màu
python3 -m http.server 8090 --directory docs          # xem trước tại http://localhost:8090
```

Thêm trang mới: tạo `src/pages/<ten>.html`, khai báo trong `PAGES` (và `NAV` nếu cần) ở `build.py`.

## Sản phẩm

- Dữ liệu 8 nhóm sản phẩm: `src/data/products.json` (tên, mô tả, thông số, sản phẩm – song ngữ `vi`/`en`).
  Mỗi nhóm tự sinh trang `/san-pham/<slug-vi>/` và `/en/products/<slug-en>/`.
- **Ảnh sản phẩm: chỉ cần thả file** vào `src/assets/img/products/<nhóm>/<id>.jpg` (hoặc .png):
  `<nhóm>` = `key` của nhóm, `<id>` = `id` của sản phẩm trong products.json; ảnh đại diện nhóm là `_group.jpg`.
  Chưa có ảnh → tự hiện khung thay thế mang thương hiệu. Nên dùng ảnh vuông, nền trắng, cạnh ≤ 800 px.
- Ảnh còn thiếu (26/11/2026): `milka/_group`, `ndc/_group`, `soy/_group`, `gelatin/meat`.

## Phát hành

Nhánh `main` = website đang chạy. Phát triển trên nhánh khác, duyệt xong mới gộp vào `main`,
gắn nhãn phiên bản (`v2.0`, `v2.1`…). GitHub Pages: *Settings → Pages → Deploy from branch → main / docs*.

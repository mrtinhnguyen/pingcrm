# RealCRM

**Hệ thống CRM Kết nối Mạng lưới Cá nhân Mã nguồn Mở — Được hỗ trợ bởi AI, Tự lưu trữ**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

Tự động đồng bộ Gmail, Telegram, Twitter/X và LinkedIn. Phát hiện sự kiện trong cuộc sống. Soạn thảo tin nhắn theo ngữ cảnh với AI. Cho bạn biết nên liên hệ với ai và tại sao.

> **[Tài liệu đầy đủ](https://docs.realcrm.vn/)** · **[Tự lưu trữ ngay](https://docs.realcrm.vn/setup)** · **[Tham gia danh sách chờ](https://realcrm.vn)**

---

## Mục lục

- [Tính năng](#tính-năng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
  - [Bước 1: Clone Repository](#bước-1-clone-repository)
  - [Bước 2: Cài đặt PostgreSQL](#bước-2-cài-đặt-postgresql)
  - [Bước 3: Cài đặt Redis](#bước-3-cài-đặt-redis)
  - [Bước 4: Thiết lập Backend](#bước-4-thiết-lập-backend)
  - [Bước 5: Thiết lập Frontend](#bước-5-thiết-lập-frontend)
  - [Bước 6: Cấu hình biến môi trường](#bước-6-cấu-hình-biến-môi-trường)
  - [Bước 7: Chạy ứng dụng](#bước-7-chạy-ứng-dụng)
- [Biến môi trường](#biến-môi-trường)
- [Cấu trúc dự án](#cấu-trúc-dự-án)

---

## Tính năng

### Bảng điều khiển (`/dashboard`)

- **Tổng số Danh bạ** — số lượng tất cả danh bạ trong CRM
- **Gợi ý đang chờ** — gợi ý theo dõi đang chờ bạn thực hiện
- **Khớp danh tính** — phát hiện danh bạ trùng lặp trên các nền tảng
- **Nên liên hệ tuần này** — top 3 danh bạ nên theo dõi, với lý do và tin nhắn do AI soạn
- **Hoạt động gần đây** — danh bạ bạn tương tác gần đây
- **Sức khỏe mối quan hệ** — phân tích danh bạ theo trạng thái (đang hoạt động, đang ấm lên, đang nguội)

### Quản lý Danh bạ

- Danh sách danh bạ phân trang, có thể sắp xếp với tìm kiếm
- **Tìm kiếm toàn văn** trên tên, email, công ty, Twitter, Telegram, tiểu sử và nội dung tin nhắn
- Lọc theo thẻ (tags)
- Chỉ báo màu sức mạnh mối quan hệ (xanh/vàng/đỏ)
- **Thao tác hàng loạt** — chọn nhiều danh bạ để thêm/xóa thẻ, đặt mức ưu tiên, gộp hoặc xóa

### Tích hợp Nền tảng

- **Gmail** — OAuth 2.0, đồng bộ email threads
- **Telegram** — MTProto client, đồng bộ chat, nhóm, tiểu sử
- **Twitter/X** — OAuth 2.0 PKCE, đồng bộ DM và mentions
- **LinkedIn** — Chrome extension để thu thập dữ liệu

### Gợi ý Theo dõi Thông minh

AI tạo gợi ý nên liên hệ với ai và tại sao:
- Kích hoạt dựa trên thờii gian (90+ ngày không tương tác)
- Kích hoạt dựa trên sự kiện (thay đổi công việc, gây quỹ)
- Soạn tin nhắn theo ngữ cảnh với Claude AI

---

## Yêu cầu hệ thống

- **Python 3.12+**
- **Node.js 18+** và npm
- **PostgreSQL 14+**
- **Redis 6+**

---

## Hướng dẫn cài đặt

### Bước 1: Clone Repository

```bash
git clone https://github.com/your-org/realcrm.git
cd realcrm
```

### Bước 2: Cài đặt PostgreSQL

#### Phương án A: PostgreSQL Local (máy tính cá nhân)

**Windows:**
1. Tải PostgreSQL từ [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Cài đặt với mật khẩu postgres (ghi nhớ mật khẩu này)
3. Mở pgAdmin hoặc psql và tạo database:

```sql
CREATE DATABASE realcrm;
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
createdb realcrm
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb realcrm
```

#### Phương án B: PostgreSQL trên Server độc lập (Remote)

Nếu PostgreSQL được cài trên server riêng, bạn chỉ cần:

1. **Tạo database trên server:**
```sql
CREATE DATABASE realcrm;
CREATE USER realcrm_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE realcrm TO realcrm_user;
```

2. **Cấu hình PostgreSQL cho kết nối từ xa** (trên server):
- Mở file `postgresql.conf`, tìm dòng `listen_addresses` và sửa thành:
```
listen_addresses = '*'
```
- Mở file `pg_hba.conf`, thêm dòng:
```
host    realcrm    realcrm_user    0.0.0.0/0    md5
```
- Restart PostgreSQL: `sudo systemctl restart postgresql`

3. **Kết nối từ máy local:** Sử dụng connection string đầy đủ trong file `.env`

### Bước 3: Cài đặt Redis

#### Phương án A: Redis Local (máy tính cá nhân)

**Windows (dùng WSL hoặc Redis for Windows):**
```bash
# Trong WSL Ubuntu
sudo apt install redis-server
sudo service redis-server start
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

Kiểm tra Redis đang chạy:
```bash
redis-cli ping
# Kết quả: PONG
```

#### Phương án B: Redis trên Server độc lập (Remote)

Nếu Redis được cài trên server riêng:

1. **Cấu hình Redis cho kết nối từ xa** (trên server):
- Mở file `redis.conf`, tìm và sửa:
```
bind 0.0.0.0
protected-mode yes
requirepass your_redis_password
```
- Restart Redis: `sudo systemctl restart redis`

2. **Kiểm tra kết nối từ máy local:**
```bash
redis-cli -h YOUR_SERVER_IP -p 6379 -a your_redis_password ping
# Kết quả: PONG
```

### Bước 4: Thiết lập Backend

```bash
cd backend

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Copy file môi trường
cp .env.example .env
```

### Bước 5: Thiết lập Frontend

```bash
cd frontend

# Cài đặt dependencies
npm install

# Copy file môi trường
cp .env.example .env.local
```

### Bước 6: Cấu hình biến môi trường

#### Backend (.env)

Mở file `backend/.env` và cấu hình:

```env
# ============================================
# CẤU HÌNH CƠ BẢN (BẮT BUỘC)
# ============================================

# Database PostgreSQL
# Format: postgresql+asyncpg://user:password@host:port/database
# 
# Ví dụ Local:
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/realcrm
#
# Ví dụ Server độc lập (Remote):
# DATABASE_URL=postgresql+asyncpg://realcrm_user:your_secure_password@your_server_ip:5432/realcrm

# Redis
# Format: redis://host:port/db hoặc redis://:password@host:port/db
#
# Ví dụ Local:
REDIS_URL=redis://localhost:6379/0
#
# Ví dụ Server độc lập (Remote) có mật khẩu:
# REDIS_URL=redis://:your_redis_password@your_server_ip:6379/0

# Secret key cho JWT - Tạo bằng lệnh:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=your_generated_secret_key_here

# Encryption key cho OAuth tokens - Tạo bằng lệnh:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your_generated_encryption_key_here

# Môi trường: development hoặc production
ENVIRONMENT=development

# ============================================
# CẤU HÌNH TÙY CHỌN
# ============================================

# Thờii gian hết hạn token (phút) - mặc định 1440 (24 giờ)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS origins cho frontend
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# ============================================
# TÍCH HỢP GOOGLE (Tùy chọn)
# ============================================

# Lấy từ Google Cloud Console:
# 1. Vào https://console.cloud.google.com/
# 2. Tạo project, enable Gmail API, Google People API, Calendar API
# 3. Credentials > Create Credentials > OAuth 2.0 Client ID
# 4. Add redirect URI: http://localhost:3000/auth/google/callback

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# ============================================
# TÍCH HỢP TWITTER/X (Tùy chọn)
# ============================================

# Lấy từ Twitter Developer Portal:
# 1. Vào https://developer.twitter.com/
# 2. Tạo project và app, enable OAuth 2.0
# 3. Set callback URL: http://localhost:3000/auth/twitter/callback

TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_REDIRECT_URI=http://localhost:3000/auth/twitter/callback
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# ============================================
# TÍCH HỢP TELEGRAM (Tùy chọn)
# ============================================

# Lấy từ my.telegram.org:
# 1. Đăng nhập bằng số điện thoại
# 2. API development tools > Create new application

TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# ============================================
# TÍCH HỢP ANTHROPIC/CLAUDE AI (Tùy chọn)
# ============================================

# Lấy từ https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key

# ============================================
# BIRD CLI - Twitter Cookie (Tùy chọn)
# ============================================

# Lấy từ browser: DevTools > Application > Cookies > x.com
AUTH_TOKEN=your_auth_token
CT0=your_ct0_token
```

#### Frontend (.env.local)

Mở file `frontend/.env.local` và cấu hình:

```env
# ============================================
# CẤU HÌNH FRONTEND
# ============================================

# URL của backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# URL của ứng dụng
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

#### Tạo khóa bảo mật

Chạy các lệnh sau để tạo khóa bảo mật:

```bash
# Trong thư mục backend với môi trường ảo đã kích hoạt

# Tạo SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Tạo ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy kết quả vào file `backend/.env` tương ứng.

#### Chạy migration database

```bash
cd backend
alembic upgrade head
```

### Bước 7: Chạy ứng dụng

Bạn cần **3-4 terminal** để chạy đầy đủ:

**Terminal 1 — Backend API:**
```bash
cd backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 — Celery Worker + Beat:**
```bash
cd backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
celery -A worker.celery_app worker --beat --loglevel=info
```

Mở [http://localhost:3000](http://localhost:3000) trong trình duyệt.

---

## Biến môi trường

| Biến | Bắt buộc | Mô tả |
|------|----------|-------|
| `SECRET_KEY` | **Có** | Khóa ký JWT. Tạo bằng: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DATABASE_URL` | **Có** | Chuỗi kết nối PostgreSQL (định dạng asyncpg) |
| `REDIS_URL` | Không | URL Redis cho Celery (mặc định: `redis://localhost:6379/0`) |
| `ENCRYPTION_KEY` | Không | Khóa Fernet để mã hóa token OAuth |
| `ENVIRONMENT` | Không | Môi trường: `development` hoặc `production` |
| `GOOGLE_CLIENT_ID` | Không | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Không | Google OAuth client secret |
| `TWITTER_CLIENT_ID` | Không | Twitter OAuth 2.0 client ID |
| `TWITTER_CLIENT_SECRET` | Không | Twitter OAuth 2.0 client secret |
| `TELEGRAM_API_ID` | Không | Telegram MTProto API ID |
| `TELEGRAM_API_HASH` | Không | Telegram MTProto API hash |
| `ANTHROPIC_API_KEY` | Không | Anthropic API key cho tính năng AI |
| `NEXT_PUBLIC_API_URL` | Không | URL backend cho frontend (mặc định: `http://localhost:8000`) |

---

## Cấu trúc dự án

```
realcrm/
├── backend/              # Python/FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic
│   │   └── integrations/ # Third-party API clients
│   ├── alembic/          # Database migrations
│   ├── tests/            # pytest tests
│   └── .env.example      # Backend environment template
│
├── frontend/             # Next.js 15 frontend (Đã Việt hóa 100%)
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # Reusable UI components
│   │   └── lib/          # Utilities
│   └── .env.example      # Frontend environment template
│
├── chrome-extension/     # LinkedIn Chrome extension
└── docs/                 # Docusaurus documentation
```

---

## License

Dự án được cấp phép theo [GNU Affero General Public License v3.0](LICENSE).

Bạn có thể tự lưu trữ, sửa đổi và phân phối RealCRM. Nếu bạn chạy phiên bản đã sửa đổi như một dịch vụ mạng, bạn phải công khai mã nguồn của mình theo cùng giấy phép.

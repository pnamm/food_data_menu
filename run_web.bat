@echo off
chcp 65001 > nul
title HỆ THỐNG QUẢN LÝ THỰC ĐƠN & SỔ KIỂM THỰC 3 BƯỚC (QĐ 1246/QĐ-BYT)

echo =========================================================================
echo    HỆ THỐNG QUẢN LÝ THỰC ĐƠN & SỔ KIỂM THỰC 3 BƯỚC - TÂN HỒ TÂY
echo    Quy chuẩn Quyết định 1246/QĐ-BYT & Thông tư 30/2012/TT-BYT
echo =========================================================================
echo.
echo Đang khởi động hệ thống web...
echo Địa chỉ truy cập: http://localhost:8000
echo.

:: Mở trình duyệt sau 2 giây
start "" http://localhost:8000

:: Chạy Web Server
python -m uvicorn app:app --host 127.0.0.1 --port 8000

pause

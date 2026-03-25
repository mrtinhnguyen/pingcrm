"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, Camera, Check, Download, Trash2 } from "lucide-react";
import { client } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export function AccountTab() {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [savingPw, setSavingPw] = useState(false);
  const [pwMsg, setPwMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const result = await client.GET("/api/v1/auth/me", {});
        const user = (result.data as any)?.data;
        if (user) {
          setDisplayName(user.full_name || "");
          setEmail(user.email || "");
        }
      } catch {}
    })();
  }, []);

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    setProfileMsg(null);
    try {
      const { error } = await client.PUT("/api/v1/auth/me" as any, {
        body: { full_name: displayName },
      });
      if (error) {
        setProfileMsg({ type: "error", text: (error as any)?.detail || "Lưu thất bại" });
      } else {
        setProfileMsg({ type: "success", text: "Đã cập nhật hồ sơ" });
        setTimeout(() => setProfileMsg(null), 3000);
      }
    } catch {
      setProfileMsg({ type: "error", text: "Lưu hồ sơ thất bại" });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    setPwMsg(null);
    if (newPw !== confirmPw) {
      setPwMsg({ type: "error", text: "Mật khẩu mới không khớp" });
      return;
    }
    if (newPw.length < 8) {
      setPwMsg({ type: "error", text: "Mật khẩu phải có ít nhất 8 ký tự" });
      return;
    }
    setSavingPw(true);
    try {
      const { error } = await client.POST("/api/v1/auth/change-password" as any, {
        body: { current_password: currentPw, new_password: newPw },
      });
      if (error) {
        setPwMsg({ type: "error", text: (error as any)?.detail || "Đổi mật khẩu thất bại" });
      } else {
        setPwMsg({ type: "success", text: "Đã cập nhật mật khẩu" });
        setCurrentPw("");
        setNewPw("");
        setConfirmPw("");
        setTimeout(() => setPwMsg(null), 3000);
      }
    } catch {
      setPwMsg({ type: "error", text: "Đổi mật khẩu thất bại" });
    } finally {
      setSavingPw(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await client.DELETE("/api/v1/auth/me" as any, {});
      localStorage.removeItem("access_token");
      window.location.href = "/auth/login";
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const initials = displayName
    ? displayName.split(" ").map((w: string) => w[0]).slice(0, 2).join("").toUpperCase()
    : "?";

  return (
    <div className="space-y-6">
      {/* Profile */}
      <div className="bg-white dark:bg-stone-900 rounded-xl border border-stone-200 dark:border-stone-700 p-5">
        <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-100 mb-1">Profile</h3>
        <p className="text-xs text-stone-500 dark:text-stone-400 mb-5">Your personal information.</p>

        <div className="flex items-start gap-5 mb-6">
          <div className="shrink-0">
            <div className="w-16 h-16 rounded-full bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300 flex items-center justify-center text-xl font-bold">
              {initials}
            </div>
          </div>
          <div className="flex-1 space-y-3">
            <div>
              <label className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-1 block">Display name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2.5 bg-white dark:bg-stone-900 text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-teal-400"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-1 block">Email</label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2.5 bg-stone-50 dark:bg-stone-800 text-stone-500 dark:text-stone-400 cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {profileMsg && (
          <p className={cn("text-xs mb-3", profileMsg.type === "success" ? "text-emerald-600 dark:text-emerald-400" : "text-red-500")}>
            {profileMsg.text}
          </p>
        )}

        <div className="flex justify-end pt-4 border-t border-stone-100 dark:border-stone-800">
          <button
            onClick={() => void handleSaveProfile()}
            disabled={savingProfile}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {savingProfile ? "Đang lưu..." : "Lưu hồ sơ"}
          </button>
        </div>
      </div>

      {/* Change Password */}
      <div className="bg-white dark:bg-stone-900 rounded-xl border border-stone-200 dark:border-stone-700 p-5">
        <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-100 mb-1">Đổi mật khẩu</h3>
        <p className="text-xs text-stone-500 dark:text-stone-400 mb-5">Cập nhật mật khẩu tài khoản của bạn.</p>

        <div className="space-y-3 max-w-sm">
          <div>
            <label className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-1 block">Mật khẩu hiện tại</label>
            <input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} placeholder="Nhập mật khẩu hiện tại" className="w-full text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2.5 bg-white dark:bg-stone-900 text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-teal-400 placeholder:text-stone-300 dark:placeholder:text-stone-600" />
          </div>
          <div>
            <label className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-1 block">Mật khẩu mới</label>
            <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="Nhập mật khẩu mới" className="w-full text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2.5 bg-white dark:bg-stone-900 text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-teal-400 placeholder:text-stone-300 dark:placeholder:text-stone-600" />
          </div>
          <div>
            <label className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-1 block">Xác nhận mật khẩu mới</label>
            <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} placeholder="Xác nhận mật khẩu mới" className="w-full text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2.5 bg-white dark:bg-stone-900 text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-teal-400 placeholder:text-stone-300 dark:placeholder:text-stone-600" />
          </div>
        </div>

        {pwMsg && (
          <p className={cn("text-xs mt-3", pwMsg.type === "success" ? "text-emerald-600 dark:text-emerald-400" : "text-red-500")}>
            {pwMsg.text}
          </p>
        )}

        <div className="flex justify-end pt-4 mt-4 border-t border-stone-100 dark:border-stone-800">
          <button
            onClick={() => void handleChangePassword()}
            disabled={savingPw || !currentPw || !newPw || !confirmPw}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {savingPw ? "Đang cập nhật..." : "Cập nhật mật khẩu"}
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white dark:bg-stone-900 rounded-xl border border-red-200 dark:border-red-800 p-5">
        <div className="flex items-center gap-2 mb-1">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <h3 className="text-sm font-semibold text-red-700 dark:text-red-400">Vùng nguy hiểm</h3>
        </div>
        <p className="text-xs text-stone-500 dark:text-stone-400 mb-5">Hành động không thể hoàn tác. Hãy cẩn thận.</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-stone-200 dark:border-stone-700 rounded-lg">
            <div>
              <p className="text-sm font-medium text-stone-700 dark:text-stone-300">Xuất tất cả dữ liệu</p>
              <p className="text-xs text-stone-400 dark:text-stone-500">Tải xuống tất cả danh bạ, tương tác và ghi chú của bạn</p>
            </div>
            <button
              onClick={() => alert("Data export is coming soon.")}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-stone-200 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800 transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Xuất
            </button>
          </div>
          <div className="flex items-center justify-between p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50/50 dark:bg-red-950/50">
            <div>
              <p className="text-sm font-medium text-red-700 dark:text-red-400">Xóa tài khoản</p>
              <p className="text-xs text-red-500/80 dark:text-red-400/80">Xóa vĩnh viễn tài khoản và tất cả dữ liệu. Không thể hoàn tác.</p>
            </div>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" /> Xóa tài khoản
            </button>
          </div>
        </div>
      </div>

      {/* Delete confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-modal="true">
          <div className="bg-white dark:bg-stone-900 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-50 dark:bg-red-950 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-stone-900 dark:text-stone-100">Xóa tài khoản của bạn?</h3>
                <p className="text-sm text-stone-500 dark:text-stone-400">Không thể hoàn tác.</p>
              </div>
            </div>
            <p className="text-sm text-stone-600 dark:text-stone-300 mb-5">
              Tất cả danh bạ, tương tác, gợi ý và tài khoản đã kết nối của bạn sẽ bị xóa vĩnh viễn.
            </p>
            <div className="flex gap-2">
              <button onClick={() => setShowDeleteConfirm(false)} className="flex-1 px-3 py-2 text-sm rounded-lg border border-stone-300 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800">Hủy</button>
              <button onClick={() => void handleDeleteAccount()} disabled={deleting} className="flex-1 px-3 py-2 text-sm rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 disabled:opacity-50">
                {deleting ? "Đang xóa..." : "Xóa tất cả"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

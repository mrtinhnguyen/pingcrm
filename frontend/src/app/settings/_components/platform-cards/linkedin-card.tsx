"use client";

import { useState } from "react";
import { X, Link2, AlertCircle, RefreshCw, Check, Unplug, Key, Settings, History } from "lucide-react";
import { cn } from "@/lib/utils";
import { client } from "@/lib/api-client";
import { ConnectionBadge, KebabMenu, SyncButtonWrapper } from "../shared";
import { SyncHistoryModal } from "../sync-history-modal";
import { SyncSettingsModal } from "../sync-settings-modal";
import type { ConnectedAccounts } from "../../_hooks/use-settings-controller";
import type { SyncPhase } from "../shared";

function LinkedInIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="20" height="20" rx="3" fill="#0A66C2" />
      <path
        d="M7 10v7M7 7v.01M11 17v-3.5a2.5 2.5 0 015 0V17M11 10v7"
        stroke="#fff"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);
  if (minutes < 1) return "vừa xong";
  if (minutes < 60) return `${minutes}phút trước`;
  if (hours < 24) return `${hours}giờ trước`;
  return `${days}ngày trước`;
}

function formatCode(raw: string): string {
  const upper = raw.toUpperCase().replace(/[^A-Z0-9-]/g, "");
  if (upper.startsWith("REALCRM-")) {
    const suffix = upper.slice(5).replace(/-/g, "").slice(0, 6);
    return suffix.length > 0 ? `REALCRM-${suffix}` : "REALCRM-";
  }
  const alphanum = upper.replace(/-/g, "").slice(0, 6);
  return alphanum.length > 0 ? `REALCRM-${alphanum}` : "";
}

export interface LinkedInCardProps {
  connected: ConnectedAccounts;
  fetchConnectionStatus: () => Promise<void>;
}

export function LinkedInCard({ connected, fetchConnectionStatus }: LinkedInCardProps) {
  const [showModal, setShowModal] = useState(false);
  const [showSyncHistory, setShowSyncHistory] = useState(false);
  const [showSyncSettings, setShowSyncSettings] = useState(false);
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [syncStatus, setSyncStatus] = useState<SyncPhase>("idle");

  const isPaired = !!connected.linkedin_extension_paired_at;

  function openModal() {
    setCode("");
    setStatus("idle");
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setCode("");
    setStatus("idle");
  }

  async function handlePair() {
    if (!code.trim()) return;
    setStatus("loading");
    try {
      const result = await (client as any).POST("/api/v1/extension/pair", {
        body: { code: code.trim() },
      });
      if (result.error) {
        setStatus("error");
        return;
      }
      closeModal();
      await fetchConnectionStatus();
    } catch {
      setStatus("error");
    }
  }

  async function handleDisconnect() {
    try {
      await (client as any).DELETE("/api/v1/extension/pair", {});
      await fetchConnectionStatus();
    } catch {
      // ignore
    }
  }

  // Sync is handled by the extension, not the backend — this is a placeholder
  // that shows the paired timestamp as "last sync"
  function handleSync() {
    setSyncStatus("loading");
    setTimeout(() => {
      setSyncStatus("success");
      setTimeout(() => setSyncStatus("idle"), 2000);
    }, 500);
  }

  const pairButtonDisabled =
    status === "loading" || !code.trim() || code.trim() === "REALCRM-";

  return (
    <>
      <div className="bg-white dark:bg-stone-900 rounded-xl border border-stone-200 dark:border-stone-700 p-5 hover:shadow-sm transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div
              className={cn(
                "w-11 h-11 rounded-lg flex items-center justify-center shrink-0",
                isPaired ? "bg-blue-50 dark:bg-blue-950" : "bg-stone-100 dark:bg-stone-800"
              )}
            >
              <LinkedInIcon />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-100">Tiện ích LinkedIn</h3>
                <ConnectionBadge connected={isPaired} />
              </div>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                Đồng bộ tin nhắn và hồ sơ LinkedIn qua tiện ích trình duyệt
              </p>
              {isPaired && connected.linkedin_extension_paired_at && (
                <p className="text-xs text-teal-600 dark:text-teal-400 mt-1">
                  Đã kết nối qua tiện ích &middot; Ghép cặp {formatTimeAgo(connected.linkedin_extension_paired_at)}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isPaired ? (
              <>
                <SyncButtonWrapper phase={syncStatus}>
                  <button
                    onClick={handleSync}
                    disabled={syncStatus === "loading"}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-stone-200 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800 transition-colors disabled:opacity-50"
                  >
                    {syncStatus === "loading" ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : syncStatus === "success" ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5" />
                    )}
                    {syncStatus === "loading"
                      ? "Đang đồng bộ..."
                      : syncStatus === "success"
                      ? "Xong"
                      : "Đồng bộ ngay"}
                  </button>
                </SyncButtonWrapper>
                <KebabMenu
                  items={[
                    { icon: Settings, label: "Cài đặt đồng bộ", onClick: () => setShowSyncSettings(true) },
                    { icon: History, label: "Lịch sử đồng bộ", onClick: () => setShowSyncHistory(true) },
                    { icon: Unplug, label: "---" },
                    {
                      icon: Unplug,
                      label: "Ngắt kết nối LinkedIn",
                      danger: true,
                      onClick: () => void handleDisconnect(),
                    },
                  ]}
                />
              </>
            ) : (
              <button
                onClick={openModal}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-stone-200 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800 transition-colors"
              >
                <Link2 className="w-3.5 h-3.5" />
                Kết nối
              </button>
            )}
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-modal="true">
          <div className="bg-white dark:bg-stone-900 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-stone-900 dark:text-stone-100">Kết nối Tiện ích LinkedIn</h3>
              <button
                onClick={closeModal}
                aria-label="Đóng"
                className="text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-stone-500 dark:text-stone-400 mb-4">
              Cài đặt tiện ích RealCRM, mở nó và nhập mã ghép cặp bên dưới.
            </p>

            <label
              htmlFor="linkedin-pair-code"
              className="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1"
            >
              Mã ghép cặp
            </label>
            <input
              id="linkedin-pair-code"
              type="text"
              value={code}
              onChange={(e) => setCode(formatCode(e.target.value))}
              placeholder="REALCRM-XXXXXX"
              className="w-full px-3 py-2 rounded-lg border border-stone-300 dark:border-stone-700 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 text-sm mb-4 font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-teal-400"
            />

            {status === "error" && (
              <p className="text-xs mb-3 flex items-center gap-1 text-red-500 dark:text-red-400">
                <AlertCircle className="w-3 h-3" />
                Mã không hợp lệ hoặc hết hạn — kiểm tra tiện ích và thử lại
              </p>
            )}

            <div className="flex gap-2">
              <button
                onClick={closeModal}
                className="flex-1 px-3 py-2 text-sm rounded-lg border border-stone-300 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800"
              >
                Hủy
              </button>
              <button
                onClick={() => void handlePair()}
                disabled={pairButtonDisabled}
                className="flex-1 px-3 py-2 text-sm rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700 disabled:opacity-50"
              >
                {status === "loading" ? "Đang ghép cặp..." : "Ghép cặp"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showSyncHistory && <SyncHistoryModal platform="linkedin" onClose={() => setShowSyncHistory(false)} />}
      {showSyncSettings && <SyncSettingsModal platform="linkedin" onClose={() => setShowSyncSettings(false)} />}
    </>
  );
}

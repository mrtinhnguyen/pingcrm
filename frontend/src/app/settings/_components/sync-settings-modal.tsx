"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Trash2, AlertTriangle, Users } from "lucide-react";
import { Toggle } from "./shared";
import { client } from "@/lib/api-client";

interface PlatformSyncConfig {
  auto_sync: boolean;
  schedule: string;
}

interface SyncSettingsModalProps {
  platform: string;
  onClose: () => void;
}

const scheduleOptions = [
  { value: "manual", label: "Chỉ thủ công" },
  { value: "6h", label: "Mỗi 6 giờ" },
  { value: "12h", label: "Mỗi 12 giờ" },
  { value: "daily", label: "Mỗi ngày một lần" },
];

export function SyncSettingsModal({ platform, onClose }: SyncSettingsModalProps) {
  const [config, setConfig] = useState<PlatformSyncConfig>({ auto_sync: true, schedule: "daily" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const { data } = await client.GET("/api/v1/settings/sync", {});
      const all = (data as any)?.data;
      if (all?.[platform]) {
        setConfig(all[platform]);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  }, [platform]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const save = async (updates: Partial<PlatformSyncConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    setIsSaving(true);
    try {
      await client.PUT("/api/v1/settings/sync", {
        body: { [platform]: newConfig },
      });
    } catch {
      setConfig(config); // revert
    } finally {
      setIsSaving(false);
    }
  };

  const platformLabel = platform.charAt(0).toUpperCase() + platform.slice(1);

  if (isLoading) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-modal="true">
      <div className="bg-white dark:bg-stone-900 rounded-xl border border-stone-200 dark:border-stone-700 shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone-100 dark:border-stone-800">
          <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-100">
            Cài đặt đồng bộ {platformLabel}
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-stone-400 dark:text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Auto-sync toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-stone-700 dark:text-stone-300">Tự động đồng bộ</p>
              <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">
                Tự động đồng bộ theo lịch
              </p>
            </div>
            <Toggle
              checked={config.auto_sync}
              onChange={(v) => void save({ auto_sync: v })}
            />
          </div>

          {/* Schedule selector */}
          {config.auto_sync && (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-stone-700 dark:text-stone-300">Lịch trình</p>
                <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">
                  Tần suất tự động đồng bộ
                </p>
              </div>
              <select
                value={config.schedule}
                onChange={(e) => void save({ schedule: e.target.value })}
                className="w-full sm:w-auto text-sm border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-1.5 text-stone-700 dark:text-stone-300 bg-white dark:bg-stone-900 focus:outline-none focus:ring-2 focus:ring-teal-400"
              >
                {scheduleOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Telegram-specific: 2nd Tier contacts */}
          {platform === "telegram" && <TelegramSyncOptions />}
        </div>
      </div>
    </div>
  );
}

/* ── Telegram-specific sync options (2nd Tier toggle + purge) ── */

function TelegramSyncOptions() {
  const [sync2ndTier, setSync2ndTier] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [tierCount, setTierCount] = useState<number | null>(null);
  const [showPurgeConfirm, setShowPurgeConfirm] = useState(false);
  const [isPurging, setIsPurging] = useState(false);
  const [purgeResult, setPurgeResult] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await client.GET("/api/v1/settings/telegram", {});
        setSync2ndTier((data as any)?.data?.sync_2nd_tier ?? true);
      } catch {}
      try {
        const { data } = await client.GET("/api/v1/contacts/2nd-tier/count", {});
        setTierCount((data as any)?.data?.count ?? 0);
      } catch {}
      setIsLoading(false);
    })();
  }, []);

  const handleToggle = async (checked: boolean) => {
    setSync2ndTier(checked);
    try {
      await client.PUT("/api/v1/settings/telegram", {
        body: { sync_2nd_tier: checked },
      });
    } catch {
      setSync2ndTier(!checked);
    }
  };

  const handlePurge = async () => {
    setIsPurging(true);
    try {
      const { data } = await client.DELETE("/api/v1/contacts/2nd-tier", {});
      const count = (data as any)?.data?.deleted_count ?? 0;
      setPurgeResult(`Đã xóa ${count} danh bạ.`);
      setTierCount(0);
    } catch {
      setPurgeResult("Xóa danh bạ thất bại.");
    } finally {
      setIsPurging(false);
      setShowPurgeConfirm(false);
    }
  };

  if (isLoading) return null;

  return (
    <>
      <div className="pt-4 border-t border-stone-100 dark:border-stone-800">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-stone-700 dark:text-stone-300">Nhập danh bạ Cấp 2</p>
            <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">
              Đồng bộ thành viên nhóm bạn chưa từng nhắn tin trực tiếp
            </p>
          </div>
          <Toggle checked={sync2ndTier} onChange={handleToggle} />
        </div>

        {tierCount !== null && tierCount > 0 && (
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-stone-400 dark:text-stone-500" />
              <p className="text-xs text-stone-600 dark:text-stone-400">
                {tierCount} danh bạ Cấp 2
              </p>
            </div>
            <button
              onClick={() => setShowPurgeConfirm(true)}
              disabled={isPurging}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-md border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3 h-3" />
              Xóa tất cả
            </button>
          </div>
        )}

        {purgeResult && (
          <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-2">{purgeResult}</p>
        )}
      </div>

      {showPurgeConfirm && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40" role="dialog" aria-modal="true">
          <div className="bg-white dark:bg-stone-900 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-50 dark:bg-red-950 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-stone-900 dark:text-stone-100">Xóa danh bạ Cấp 2</h3>
                <p className="text-sm text-stone-500 dark:text-stone-400">Không thể hoàn tác.</p>
              </div>
            </div>
            <p className="text-sm text-stone-600 dark:text-stone-300 mb-5">
              Hành động này sẽ xóa vĩnh viễn <strong>{tierCount}</strong> danh bạ Cấp 2.
            </p>
            <div className="flex gap-2">
              <button onClick={() => setShowPurgeConfirm(false)} className="flex-1 px-3 py-2 text-sm rounded-lg border border-stone-300 dark:border-stone-700 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800">Hủy</button>
              <button onClick={() => void handlePurge()} disabled={isPurging} className="flex-1 px-3 py-2 text-sm rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 disabled:opacity-50">
                {isPurging ? "Đang xóa..." : `Xóa ${tierCount} danh bạ`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

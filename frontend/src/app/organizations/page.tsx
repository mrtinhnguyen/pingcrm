"use client";

export const dynamic = "force-dynamic";

import { Suspense, useState, useCallback, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Search, Building2, ChevronDown, ChevronRight, CheckSquare, Tag, X, Archive, GitMerge, BarChart3, MessageSquare, Clock } from "lucide-react";
import Link from "next/link";
import { client } from "@/lib/api-client";
import { ContactAvatar } from "@/components/contact-avatar";
import { ScoreBadge } from "@/components/score-badge";
import { formatDistanceToNow } from "date-fns";

interface OrgContact {
  id: string;
  full_name: string | null;
  given_name: string | null;
  family_name: string | null;
  title: string | null;
  avatar_url: string | null;
  relationship_score: number;
  last_interaction_at: string | null;
}

interface Organization {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  location: string | null;
  website: string | null;
  linkedin_url: string | null;
  twitter_handle: string | null;
  notes: string | null;
  contact_count: number;
  avg_relationship_score: number;
  total_interactions: number;
  last_interaction_at: string | null;
  contacts: OrgContact[] | null;
}

function MergeModal({
  orgs,
  onMerge,
  onClose,
  isPending,
}: {
  orgs: Organization[];
  onMerge: (targetId: string) => void;
  onClose: () => void;
  isPending: boolean;
}) {
  const [targetId, setTargetId] = useState(orgs[0]?.id ?? "");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 mb-4">
          <GitMerge className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-bold text-gray-900">Merge Organizations</h2>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          All contacts from the selected organizations will be moved under one organization. Select which to keep:
        </p>

        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Keep as target organization:
          </label>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {orgs.map((org) => (
              <label
                key={org.id}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                  targetId === org.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <input
                  type="radio"
                  name="target"
                  checked={targetId === org.id}
                  onChange={() => setTargetId(org.id)}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-900">{org.name}</span>
                <span className="text-xs text-gray-400 ml-auto">{org.contact_count} contacts</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => targetId && onMerge(targetId)}
            disabled={!targetId || isPending}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <GitMerge className="w-4 h-4" />
            {isPending ? "Merging..." : "Merge"}
          </button>
        </div>
      </div>
    </div>
  );
}

function BulkActionBar({
  selectedCount,
  selectedOrgCount,
  allTags,
  onAddTag,
  onRemoveTag,
  onSetPriority,
  onMergeOrgs,
  onClear,
  isPending,
}: {
  selectedCount: number;
  selectedOrgCount: number;
  allTags: string[];
  onAddTag: (tag: string) => void;
  onRemoveTag: (tag: string) => void;
  onSetPriority: (level: string) => void;
  onMergeOrgs: () => void;
  onClear: () => void;
  isPending: boolean;
}) {
  const [tagInput, setTagInput] = useState("");
  const [showTagDropdown, setShowTagDropdown] = useState(false);
  const [tagMode, setTagMode] = useState<"add" | "remove">("add");

  const filteredTags = allTags.filter(
    (t) => !tagInput || t.toLowerCase().includes(tagInput.toLowerCase())
  );

  return (
    <div className="sticky top-14 z-30 bg-blue-600 text-white px-4 py-2.5 rounded-lg mb-4 flex items-center gap-3 shadow-lg">
      <div className="flex items-center gap-2 flex-shrink-0">
        <CheckSquare className="w-4 h-4" />
        <span className="text-sm font-medium">{selectedCount} selected</span>
      </div>

      <div className="h-5 w-px bg-blue-400" />

      <div className="relative">
        <div className="flex items-center gap-1">
          <button
            onClick={() => { setTagMode("add"); setShowTagDropdown((v) => !v); }}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-blue-500 hover:bg-blue-400 transition-colors"
          >
            <Tag className="w-3 h-3" />
            Add Tag
          </button>
          <button
            onClick={() => { setTagMode("remove"); setShowTagDropdown((v) => !v); }}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-blue-500 hover:bg-blue-400 transition-colors"
          >
            <X className="w-3 h-3" />
            Remove Tag
          </button>
        </div>

        {showTagDropdown && (
          <div className="absolute left-0 top-full mt-1 w-56 bg-white rounded-lg border border-gray-200 shadow-lg z-50 p-2">
            <input
              type="text"
              placeholder={tagMode === "add" ? "Type tag name..." : "Select tag to remove..."}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && tagInput.trim() && tagMode === "add") {
                  onAddTag(tagInput.trim());
                  setTagInput("");
                  setShowTagDropdown(false);
                }
              }}
              className="w-full px-2.5 py-1.5 text-sm text-gray-900 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400 mb-1"
              autoFocus
            />
            <div className="max-h-32 overflow-y-auto">
              {filteredTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => {
                    if (tagMode === "add") onAddTag(tag);
                    else onRemoveTag(tag);
                    setTagInput("");
                    setShowTagDropdown(false);
                  }}
                  className="w-full text-left px-2.5 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                >
                  {tagMode === "add" ? "+" : "-"} {tag}
                </button>
              ))}
              {tagMode === "add" && tagInput.trim() && !allTags.includes(tagInput.trim()) && (
                <button
                  onClick={() => {
                    onAddTag(tagInput.trim());
                    setTagInput("");
                    setShowTagDropdown(false);
                  }}
                  className="w-full text-left px-2.5 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-md font-medium"
                >
                  + Create &quot;{tagInput.trim()}&quot;
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="h-5 w-px bg-blue-400" />

      <button
        onClick={() => onSetPriority("archived")}
        disabled={isPending}
        className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-blue-500 hover:bg-blue-400 transition-colors disabled:opacity-50"
      >
        <Archive className="w-3 h-3" />
        Archive All
      </button>

      {selectedOrgCount >= 2 && (
        <>
          <div className="h-5 w-px bg-blue-400" />
          <button
            onClick={onMergeOrgs}
            disabled={isPending}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50"
          >
            <GitMerge className="w-3 h-3" />
            Merge {selectedOrgCount} Orgs
          </button>
        </>
      )}

      <div className="flex-1" />

      <button
        onClick={onClear}
        className="text-xs text-blue-200 hover:text-white underline"
      >
        Clear selection
      </button>
    </div>
  );
}

function OrganizationsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchFromUrl = searchParams.get("q") ?? "";
  const [searchInput, setSearchInput] = useState(searchFromUrl);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const page = Number(searchParams.get("page") ?? "1");

  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedOrgIds, setSelectedOrgIds] = useState<Set<string>>(new Set());
  const [showMergeModal, setShowMergeModal] = useState(false);

  const setParams = useCallback(
    (updates: Record<string, string | undefined>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value) params.set(key, value);
        else params.delete(key);
      }
      if (!("page" in updates)) params.delete("page");
      router.replace(`/organizations?${params.toString()}`, { scroll: false });
    },
    [searchParams, router]
  );

  const { data, isLoading, isError } = useQuery({
    queryKey: ["organizations", searchFromUrl, page],
    queryFn: async () => {
      const params: Record<string, string> = { page: String(page), page_size: "50" };
      if (searchFromUrl) params.search = searchFromUrl;
      const { data } = await client.GET("/api/v1/organizations" as any, {
        params: { query: params },
      });
      return data as { data: Organization[]; meta: { total: number; page: number; page_size: number; total_pages: number } };
    },
  });

  const { data: allTags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: async () => {
      const { data } = await client.GET("/api/v1/contacts/tags");
      return (data?.data as string[]) ?? [];
    },
  });

  const organizations = data?.data ?? [];
  const meta = data?.meta;

  const bulkUpdate = useMutation({
    mutationFn: async (body: {
      contact_ids: string[];
      add_tags?: string[];
      remove_tags?: string[];
      priority_level?: string;
    }) => {
      const { data, error } = await client.POST("/api/v1/contacts/bulk-update" as any, {
        body,
      });
      if (error) throw new Error((error as { detail?: string })?.detail ?? "Bulk update failed");
      return data;
    },
    onSuccess: () => {
      setSelectedIds(new Set());
      void queryClient.invalidateQueries({ queryKey: ["organizations"] });
      void queryClient.invalidateQueries({ queryKey: ["contacts"] });
      void queryClient.invalidateQueries({ queryKey: ["tags"] });
    },
  });

  const mergeOrgs = useMutation({
    mutationFn: async (body: { source_ids: string[]; target_id: string }) => {
      const { data, error } = await client.POST("/api/v1/organizations/merge" as any, { body });
      if (error) throw new Error((error as { detail?: string })?.detail ?? "Merge failed");
      return data;
    },
    onSuccess: () => {
      setSelectedIds(new Set());
      setSelectedOrgIds(new Set());
      setShowMergeModal(false);
      void queryClient.invalidateQueries({ queryKey: ["organizations"] });
      void queryClient.invalidateQueries({ queryKey: ["contacts"] });
    },
  });

  const toggleOrg = (orgId: string) => {
    setExpandedOrgs((prev) => {
      const next = new Set(prev);
      if (next.has(orgId)) next.delete(orgId);
      else next.add(orgId);
      return next;
    });
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectOrg = (org: Organization) => {
    const contacts = org.contacts ?? [];
    const orgContactIds = contacts.map((c) => c.id);
    const allSelected = orgContactIds.length > 0 && orgContactIds.every((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        orgContactIds.forEach((id) => next.delete(id));
      } else {
        orgContactIds.forEach((id) => next.add(id));
      }
      return next;
    });
    setSelectedOrgIds((prev) => {
      const next = new Set(prev);
      if (allSelected) next.delete(org.id);
      else next.add(org.id);
      return next;
    });
  };

  const selectedArray = Array.from(selectedIds);
  const selectedMergeOrgs = organizations.filter((o) => selectedOrgIds.has(o.id));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
            {meta && (
              <p className="text-sm text-gray-500 mt-0.5">
                {meta.total} organizations
              </p>
            )}
          </div>
        </div>

        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search organizations..."
              value={searchInput}
              onChange={(e) => {
                const value = e.target.value;
                setSearchInput(value);
                if (debounceRef.current) clearTimeout(debounceRef.current);
                debounceRef.current = setTimeout(() => {
                  setParams({ q: value || undefined });
                }, 300);
              }}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>

        {/* Bulk action bar */}
        {selectedIds.size > 0 && (
          <BulkActionBar
            selectedCount={selectedIds.size}
            selectedOrgCount={selectedOrgIds.size}
            allTags={allTags}
            isPending={bulkUpdate.isPending}
            onAddTag={(tag) =>
              bulkUpdate.mutate({ contact_ids: selectedArray, add_tags: [tag] })
            }
            onRemoveTag={(tag) =>
              bulkUpdate.mutate({ contact_ids: selectedArray, remove_tags: [tag] })
            }
            onSetPriority={(level) =>
              bulkUpdate.mutate({ contact_ids: selectedArray, priority_level: level })
            }
            onMergeOrgs={() => setShowMergeModal(true)}
            onClear={() => { setSelectedIds(new Set()); setSelectedOrgIds(new Set()); }}
          />
        )}

        {showMergeModal && selectedMergeOrgs.length >= 2 && (
          <MergeModal
            orgs={selectedMergeOrgs}
            isPending={mergeOrgs.isPending}
            onMerge={(targetId) => {
              const sourceIds = selectedMergeOrgs.map((o) => o.id).filter((id) => id !== targetId);
              mergeOrgs.mutate({ source_ids: sourceIds, target_id: targetId });
            }}
            onClose={() => setShowMergeModal(false)}
          />
        )}

        {isLoading && (
          <div className="text-center py-12 text-gray-400">Loading organizations...</div>
        )}

        {isError && (
          <div className="text-center py-12 text-red-500">
            Failed to load organizations.
          </div>
        )}

        {!isLoading && !isError && organizations.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            No organizations found.
          </div>
        )}

        {organizations.length > 0 && (
          <div className="space-y-2">
            {organizations.map((org) => {
              const contacts = org.contacts ?? [];
              const isExpanded = expandedOrgs.has(org.id);
              const orgContactIds = contacts.map((c) => c.id);
              const allOrgSelected = orgContactIds.length > 0 && orgContactIds.every((id) => selectedIds.has(id));
              const someOrgSelected = orgContactIds.some((id) => selectedIds.has(id));
              return (
                <div key={org.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors">
                    <input
                      type="checkbox"
                      checked={allOrgSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = someOrgSelected && !allOrgSelected;
                      }}
                      onChange={() => toggleSelectOrg(org)}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 flex-shrink-0"
                      aria-label={`Select all contacts in ${org.name}`}
                    />
                    <button
                      onClick={() => toggleOrg(org.id)}
                      className="flex items-center gap-3 flex-1 min-w-0 text-left"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      )}
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                        <Building2 className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link
                          href={`/organizations/${org.id}`}
                          className="text-sm font-semibold text-gray-900 hover:text-blue-600"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {org.name}
                        </Link>
                        {org.domain && (
                          <span className="ml-2 text-xs text-gray-400">{org.domain}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 flex-shrink-0">
                        <span className="text-xs text-gray-500" title="Contacts">
                          {org.contact_count} {org.contact_count === 1 ? "person" : "people"}
                        </span>
                        {org.avg_relationship_score > 0 && (
                          <span className="text-xs text-gray-500 flex items-center gap-1" title="Avg Score">
                            <BarChart3 className="w-3 h-3" />
                            {org.avg_relationship_score}
                          </span>
                        )}
                        {org.total_interactions > 0 && (
                          <span className="text-xs text-gray-500 flex items-center gap-1" title="Total Interactions">
                            <MessageSquare className="w-3 h-3" />
                            {org.total_interactions}
                          </span>
                        )}
                        {org.last_interaction_at && (
                          <span className="text-xs text-gray-400 flex items-center gap-1" title="Last Activity">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(org.last_interaction_at), { addSuffix: true })}
                          </span>
                        )}
                      </div>
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-100">
                      <table className="w-full text-sm">
                        <tbody className="divide-y divide-gray-50">
                          {contacts.map((contact) => {
                            const name =
                              contact.full_name ??
                              [contact.given_name, contact.family_name].filter(Boolean).join(" ") ??
                              "Unnamed";
                            const isSelected = selectedIds.has(contact.id);
                            return (
                              <tr key={contact.id} className={`hover:bg-gray-50 ${isSelected ? "bg-blue-50" : ""}`}>
                                <td className="w-10 px-4 py-2.5 pl-14">
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => toggleSelect(contact.id)}
                                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    aria-label={`Select ${name}`}
                                  />
                                </td>
                                <td className="px-4 py-2.5">
                                  <Link
                                    href={`/contacts/${contact.id}`}
                                    className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium"
                                  >
                                    <ContactAvatar
                                      avatarUrl={contact.avatar_url}
                                      name={name}
                                      size="xs"
                                    />
                                    {name}
                                  </Link>
                                </td>
                                <td className="px-4 py-2.5 text-gray-500">
                                  {contact.title ?? "-"}
                                </td>
                                <td className="px-4 py-2.5">
                                  <ScoreBadge score={contact.relationship_score} lastInteractionAt={contact.last_interaction_at} />
                                </td>
                                <td className="px-4 py-2.5 text-gray-500 text-right">
                                  {contact.last_interaction_at
                                    ? formatDistanceToNow(new Date(contact.last_interaction_at), { addSuffix: true })
                                    : "Never"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {meta && meta.total_pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <button
              disabled={page <= 1}
              onClick={() => setParams({ page: String(page - 1) })}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
            >
              Previous
            </button>
            <span className="text-sm text-gray-500">
              Page {page} of {meta.total_pages}
            </span>
            <button
              disabled={page >= meta.total_pages}
              onClick={() => setParams({ page: String(page + 1) })}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function PageLoading() {
  return <div className="min-h-screen bg-stone-50 flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-teal-500 border-t-transparent rounded-full" /></div>;
}

export default function OrganizationsPage() {
  return <Suspense fallback={<PageLoading />}><OrganizationsPageContent /></Suspense>;
}

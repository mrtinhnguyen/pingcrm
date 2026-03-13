"use client";

import { useState, memo } from "react";
import { Building2 } from "lucide-react";

const COMMON_DOMAINS = new Set([
  "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
  "icloud.com", "mail.com", "protonmail.com", "aol.com",
  "live.com", "me.com", "msn.com", "yandex.com",
]);

/** Extract a company domain from an email list (skips common providers). */
function domainFromEmails(emails: string[] | null | undefined): string | null {
  if (!emails?.length) return null;
  for (const email of emails) {
    const domain = email.split("@")[1]?.toLowerCase();
    if (domain && !COMMON_DOMAINS.has(domain)) return domain;
  }
  return null;
}

interface CompanyFaviconProps {
  /** Organization domain (preferred, used directly). */
  domain?: string | null;
  /** Contact emails — domain is derived from the first non-common email. */
  emails?: string[] | null;
  /** Icon size class (default: "w-4 h-4"). */
  size?: string;
  /** Additional CSS classes on the wrapper. */
  className?: string;
}

export const CompanyFavicon = memo(function CompanyFavicon({
  domain,
  emails,
  size = "w-4 h-4",
  className,
}: CompanyFaviconProps) {
  const [failed, setFailed] = useState(false);
  const resolvedDomain = domain || domainFromEmails(emails);

  if (!resolvedDomain || failed) {
    return <Building2 className={`${size} text-zinc-400 ${className ?? ""}`} />;
  }

  return (
    <img
      src={`https://www.google.com/s2/favicons?domain=${encodeURIComponent(resolvedDomain)}&sz=32`}
      alt=""
      className={`${size} rounded-sm ${className ?? ""}`}
      onError={() => setFailed(true)}
    />
  );
});

export { domainFromEmails };

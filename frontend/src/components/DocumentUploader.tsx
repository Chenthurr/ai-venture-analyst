"use client";

import { useRef, useState } from "react";
import { DocumentOut } from "@/types";
import { Button, SectionLabel, Tag, Select } from "@/components/ui";

const CATEGORIES = [
  "pitch_deck",
  "financials",
  "market_report",
  "cap_table",
  "legal",
  "customer_survey",
  "other",
];

function statusTone(status: DocumentOut["status"]) {
  if (status === "embedded") return "positive";
  if (status === "failed") return "negative";
  return "gold";
}

export function DocumentUploader({
  documents,
  onUpload,
  onDelete,
  uploading,
}: {
  documents: DocumentOut[];
  onUpload: (file: File, category: string) => void;
  onDelete: (id: string) => void;
  uploading?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [category, setCategory] = useState("pitch_deck");
  const [dragOver, setDragOver] = useState(false);

  return (
    <div>
      <SectionLabel number="03" title="Documents" />

      <div className="flex items-end gap-3 mb-4">
        <Select label="Category for next upload" value={category} onChange={(e) => setCategory(e.target.value)} className="w-64">
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c.replace("_", " ")}
            </option>
          ))}
        </Select>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) onUpload(file, category);
        }}
        onClick={() => inputRef.current?.click()}
        className={`border border-dashed rounded p-8 text-center cursor-pointer transition-colors ${
          dragOver ? "border-gold bg-gold/5" : "border-ink-border hover:border-paper-faint"
        }`}
      >
        <p className="text-sm text-paper-muted">
          Drop a file here, or click to browse
        </p>
        <p className="text-xs text-paper-faint mt-1">PDF, PPTX, XLSX, CSV, TXT, MD</p>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".pdf,.pptx,.xlsx,.xlsm,.csv,.txt,.md"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file, category);
            e.target.value = "";
          }}
        />
      </div>

      {uploading && <p className="text-xs text-gold mt-2">Uploading & parsing…</p>}

      <div className="mt-4 divide-y divide-ink-border border border-ink-border rounded">
        {documents.length === 0 && (
          <p className="p-4 text-sm text-paper-faint italic">No documents uploaded yet.</p>
        )}
        {documents.map((doc) => (
          <div key={doc.id} className="flex items-center justify-between p-3">
            <div>
              <div className="text-sm text-paper">{doc.filename}</div>
              <div className="text-xs text-paper-faint mt-0.5">
                {doc.doc_category || "uncategorized"} · {doc.file_type}
              </div>
              {doc.error_message && (
                <div className="text-xs text-signal-negative mt-1">{doc.error_message}</div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Tag tone={statusTone(doc.status) as any}>{doc.status}</Tag>
              <button
                onClick={() => onDelete(doc.id)}
                className="text-xs text-paper-faint hover:text-signal-negative"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useState, useRef } from "react";
import { useEffect } from "react";
import { Upload, X, File, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadedDocument {
  id: string;
  filename: string;
  file_type: string;
  chunks_created: number;
}

interface DocumentUploaderProps {
  onDocumentsSelected: (documentIds: string[]) => void;
}

export function DocumentUploader({ onDocumentsSelected }: DocumentUploaderProps) {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      const file = files[0]; // Handle one file at a time
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Upload failed");
      }

      const data = await response.json();
      
      if (data.success) {
        const newDoc: UploadedDocument = {
          id: data.document_id,
          filename: data.filename,
          file_type: data.file_type,
          chunks_created: data.chunks_created,
        };
        // If a document with same filename already exists, replace it (avoid duplicates)
        const existingIndex = documents.findIndex((d) => d.filename === newDoc.filename);
        let updatedDocs: UploadedDocument[];
        if (existingIndex >= 0) {
          updatedDocs = [...documents];
          updatedDocs[existingIndex] = newDoc;
        } else {
          updatedDocs = [...documents, newDoc];
        }
        setDocuments(updatedDocs);
        onDocumentsSelected(updatedDocs.map((d) => d.id));
      } else {
        throw new Error("Upload failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleRemoveDocument = (documentId: string) => {
    // Optimistically remove from UI, call backend, restore on failure
    const before = documents;
    const updatedDocs = documents.filter((d) => d.id !== documentId);
    setDocuments(updatedDocs);
    onDocumentsSelected(updatedDocs.map((d) => d.id));

    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/documents/${documentId}`, {
          method: "DELETE",
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((data && (data.detail || data.error)) || "Failed to delete document");
        }

        // If backend returned multiple removed IDs, remove them from UI
        const removedIds: string[] = data.removed_doc_ids || [];
        if (removedIds.length > 0) {
          const filtered = documents.filter((d) => !removedIds.includes(d.id));
          setDocuments(filtered);
          onDocumentsSelected(filtered.map((d) => d.id));
        }
      } catch (err) {
        // Restore previous state on error
        setDocuments(before);
        onDocumentsSelected(before.map((d) => d.id));
        setError(err instanceof Error ? err.message : "Failed to delete document");
      }
    })();
  };

  // Sync with backend on mount to load any previously uploaded documents
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
          const res = await fetch(`${API_URL}/api/documents`);
        if (!res.ok) return;
        const data = await res.json();
        if (!mounted) return;
        if (Array.isArray(data.documents) && data.documents.length > 0) {
          const remoteDocs: UploadedDocument[] = data.documents.map((item: any) => {
            if (typeof item === "string") {
              return { id: item, filename: item, file_type: "", chunks_created: 0 };
            }
            return {
              id: item.id,
              filename: item.filename || item.id,
              file_type: "",
              chunks_created: item.chunks_created || 0,
            };
          });
          setDocuments(remoteDocs);
          onDocumentsSelected(remoteDocs.map((d) => d.id));
        }
      } catch (e) {
        // ignore sync errors
      }
    })();

    return () => {
      mounted = false;
    };
  }, [onDocumentsSelected]);

  return (
    <div className="border border-border rounded-lg p-4 bg-card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <File className="w-4 h-4" />
          Reference Documents ({documents.length})
        </h3>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.png,.jpg,.jpeg,.gif,.webp"
          className="hidden"
          disabled={uploading}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="gap-2"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-2 mb-3 rounded bg-destructive/10 border border-destructive/20">
          <AlertCircle className="w-4 h-4 text-destructive shrink-0" />
          <span className="text-xs text-destructive">{error}</span>
        </div>
      )}

      {documents.length > 0 && (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-2 rounded bg-muted text-sm"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{doc.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {doc.file_type} • {doc.chunks_created} chunks
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleRemoveDocument(doc.id)}
                className="shrink-0 h-8 w-8"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {documents.length === 0 && !error && (
        <p className="text-xs text-muted-foreground text-center py-4">
          No documents uploaded. Click Upload to add reference documents.
        </p>
      )}

      <p className="text-xs text-muted-foreground mt-3">
        Supported: PDF, Word, Excel, CSV, TXT, Images
      </p>
    </div>
  );
}
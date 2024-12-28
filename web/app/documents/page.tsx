"use client";

import { useState } from "react";
import FileUpload from "@/components/FileUpload";

export default function UploadPage() {
  const [uploadedUrls, setUploadedUrls] = useState<string[]>([]);

  const handleUploadComplete = (url: string) => {
    setUploadedUrls((prev) => [...prev, url]);
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">PDF Upload</h1>

      <div className="mb-8">
        <FileUpload
          onUploadComplete={handleUploadComplete}
          bucketName="documents"
        />
      </div>

      {uploadedUrls.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Uploaded PDFs:</h2>
          <ul className="space-y-2">
            {uploadedUrls.map((url, index) => (
              <li key={index} className="flex items-center space-x-2">
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  PDF Document {index + 1}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

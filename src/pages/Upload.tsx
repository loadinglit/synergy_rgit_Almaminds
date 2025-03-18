import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload as UploadIcon } from "lucide-react";
import { Card, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export const Upload = () => {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState("");

  const onDrop = useCallback((acceptedFiles: File[]) => {
    console.log(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/*": [".mp4", ".mov", ".avi", ".mkv"],
    },
  });

  const handleAnalyzeVideo = async () => {
    if (!youtubeUrl.trim()) {
      setError("Please enter a valid YouTube URL.");
      return;
    }
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/analyze/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: youtubeUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process video.");
      }

      const data = await response.json();
      setVideoData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-red-600">
        Upload Your Video
      </h1>

      <Card>
        <CardTitle className="text-red-600">Upload Video</CardTitle>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
              ${
                isDragActive
                  ? "border-red-500 bg-red-50"
                  : "border-gray-300 hover:border-red-500"
              }`}
          >
            <input {...getInputProps()} />
            <UploadIcon className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-lg mb-2 text-gray-700">
              {isDragActive
                ? "Drop your video here"
                : "Drag & drop your video here"}
            </p>
            <p className="text-sm text-gray-500 mb-4">or</p>
            <center>
              <Button
                type="button"
                className="bg-red-500 text-white hover:bg-red-700 transition"
              >
                Browse Files
              </Button>
            </center>
          </div>

          {/* YouTube URL Input */}
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-red-600">
              Or paste a YouTube URL
            </h3>
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="https://youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <Button
                onClick={handleAnalyzeVideo}
                disabled={loading}
                className="bg-red-500 text-white hover:bg-red-700 transition"
              >
                {loading ? "Processing..." : "Process URL"}
              </Button>
            </div>
            {error && <p className="text-red-500 mt-2">{error}</p>}
          </div>

          {/* Display Video Analysis Results */}
          {videoData && (
            <div className="mt-8 p-4 border rounded-lg bg-gray-100">
              <h3 className="text-lg font-semibold text-red-600">
                Video Analysis Result
              </h3>
              <p>
                <strong>Title:</strong> {videoData.title}
              </p>
              <p>
                <strong>Summary:</strong> {videoData.summary}
              </p>
              <p>
                <strong>Keywords:</strong> {videoData.keywords?.join(", ")}
              </p>

              {/* Display Highlights */}
              {videoData.highlights?.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold text-red-500">Highlights:</h4>
                  <ul className="list-disc pl-5">
                    {videoData.highlights.map(
                      (highlight: any, index: number) => (
                        <li key={index}>
                          {highlight.text} ({highlight.start_time} -{" "}
                          {highlight.end_time})
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

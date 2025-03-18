import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon } from 'lucide-react';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const Upload = () => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Handle file upload logic here
    console.log(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
    },
  });

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-red-600">Upload Your Video</h1>

      <Card>
        <CardTitle className="text-red-600">Upload Video</CardTitle>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
              ${
                isDragActive
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-300 hover:border-red-500'
              }`}
          >
            <input {...getInputProps()} />
            <UploadIcon className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-lg mb-2 text-gray-700">
              {isDragActive
                ? 'Drop your video here'
                : 'Drag & drop your video here'}
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

          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-red-600">
              Or paste a YouTube URL
            </h3>
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="https://youtube.com/watch?v=..."
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <Button className="bg-red-500 text-white hover:bg-red-700 transition">
                Process URL
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

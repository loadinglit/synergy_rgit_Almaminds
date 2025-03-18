import React from 'react';
import { Download } from 'lucide-react';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const Results = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-red-600">Generated Results</h1>

      <div className="grid md:grid-cols-2 gap-8">
        {/* AI-Generated Shorts Section */}
        <Card>
          <CardTitle className="text-red-600">AI-Generated Shorts</CardTitle>
          <CardContent>
            <div className="space-y-4">
              {/* Video Placeholder */}
              <div className="aspect-video bg-red-50 border-2 border-red-400 rounded-lg flex items-center justify-center">
                <p className="text-red-500">Video Preview</p>
              </div>

              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold text-red-700">Highlight #1</h4>
                  <p className="text-sm text-red-500">Duration: 0:30</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-red-500 text-red-600 hover:bg-red-500 hover:text-white"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Results Section */}
        <Card>
          <CardTitle className="text-red-600">Processing Results</CardTitle>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-300 rounded-lg">
                <h4 className="font-semibold mb-2 text-red-700">Analysis Summary</h4>
                <ul className="text-sm text-red-600 space-y-2">
                  <li>• 3 key moments identified</li>
                  <li>• 2 highlight clips generated</li>
                  <li>• 5 ad variations created</li>
                </ul>
              </div>

              <Button
                className="w-full bg-red-500 text-white hover:bg-red-700 transition"
              >
                Generate More Variations
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

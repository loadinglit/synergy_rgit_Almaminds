import React from 'react';
import { Copy, Download } from 'lucide-react';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const AdCreatives = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-red-600">Ad Creatives</h1>

      <div className="grid gap-8">
        <Card className="border-red-400">
          <CardTitle className="text-red-600">Generated Ad Variations</CardTitle>
          <CardContent>
            <div className="space-y-6">
              {/* Ad Creative Example */}
              <div className="border border-red-400 rounded-lg p-6 bg-red-50">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-xl mb-2 text-red-700">Transform Your Content with AI</h3>
                    <p className="text-red-600">
                      Generate engaging shorts and compelling ads automatically with our advanced AI technology.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-red-500 text-red-600 hover:bg-red-500 hover:text-white"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-red-500 text-red-600 hover:bg-red-500 hover:text-white"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                  </div>
                </div>

                {/* Headlines and Descriptions Section */}
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                    <h4 className="font-medium mb-2 text-red-700">Headlines</h4>
                    <ul className="text-sm space-y-2 text-red-600">
                      <li>• Boost Your Content Strategy with AI</li>
                      <li>• Create Viral Shorts Automatically</li>
                      <li>• Scale Your Content Production</li>
                    </ul>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                    <h4 className="font-medium mb-2 text-red-700">Descriptions</h4>
                    <ul className="text-sm space-y-2 text-red-600">
                      <li>• AI-powered video processing for content creators</li>
                      <li>• Generate engaging shorts in minutes</li>
                      <li>• Optimize your ad performance with AI</li>
                    </ul>
                  </div>
                </div>
              </div>

              <Button
                className="w-full bg-red-500 text-white hover:bg-red-700 transition"
              >
                Generate More Ad Variations
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

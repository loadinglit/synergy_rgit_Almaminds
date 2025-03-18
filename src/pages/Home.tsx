import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, FastForward, Wand2 } from 'lucide-react';
import { motion } from 'framer-motion';
import Particles from 'react-tsparticles';
import { loadFull } from 'tsparticles';
import { Button } from '../components/ui/Button';

export const Home = () => {
  const navigate = useNavigate();

  // Particle options for animated background
  const particlesInit = async (main) => {
    await loadFull(main);
  };

  const particlesLoaded = (container) => {};

  // Timeline steps data
  const timelineSteps = [
    {
      title: 'Upload Your Video',
      description: 'Begin by uploading your video to the platform. Our AI will process it to detect key highlights.',
      icon: <Play className="w-8 h-8 text-red-500" />,
    },
    {
      title: 'AI Processing',
      description: 'AI identifies engaging moments, extracts highlights, and prepares the content for shorts or ads.',
      icon: <FastForward className="w-8 h-8 text-red-500" />,
    },
    {
      title: 'Generate Short Clips',
      description: 'The platform automatically converts the highlights into short, engaging videos.',
      icon: <Wand2 className="w-8 h-8 text-red-500" />,
    },
    {
      title: 'AI Ad Creation',
      description: 'Compelling ad creatives with AI-powered copywriting and visuals are generated.',
      icon: <Wand2 className="w-8 h-8 text-red-500" />,
    },
    {
      title: 'Publish & Scale',
      description: 'Export your content and share it across multiple platforms to engage your audience.',
      icon: <Play className="w-8 h-8 text-red-500" />,
    },
  ];

  return (
    <div className="relative space-y-20 bg-white text-gray-900 overflow-hidden">
      {/* Particle Background */}
      <Particles
        id="tsparticles"
        init={particlesInit}
        loaded={particlesLoaded}
        options={{
          background: {
            color: '#fff',
          },
          fpsLimit: 60,
          particles: {
            number: {
              value: 100,
            },
            color: {
              value: ['#FF0000', '#FF6347'], // Shades of Red
            },
            shape: {
              type: 'circle',
            },
            opacity: {
              value: 0.7,
              random: true,
            },
            size: {
              value: { min: 1, max: 3 },
              random: true,
            },
            move: {
              enable: true,
              speed: 1,
              direction: 'top',
              random: false,
              straight: false,
              outModes: {
                default: 'out',
              },
            },
          },
          interactivity: {
            events: {
              onHover: {
                enable: true,
                mode: 'repulse',
              },
              resize: true,
            },
          },
          detectRetina: true,
        }}
        className="absolute inset-0 z-0"
      />

      {/* Hero Section */}
      <section className="relative text-center space-y-8 py-16 z-10">
        <h1 className="text-6xl font-bold text-gray-900">Transform Your Videos with AI</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Generate engaging short-form content and compelling ad creatives automatically using our advanced AI technology.
        </p>
        <center>
          <motion.div>
            <Button
              size="lg"
              className="bg-red-500 text-white hover:bg-red-700 transition-all"
              onClick={() => navigate('/upload')}
            >
              Get Started Now
            </Button>
          </motion.div>
        </center>
      </section>

      {/* Features Section */}
      <section className="relative grid md:grid-cols-3 gap-8 z-10">
        {timelineSteps.slice(0, 3).map((step, index) => (
          <motion.div
            key={index}
            className="text-center space-y-4 p-6 bg-white rounded-lg shadow-md border border-gray-200 hover:border-red-500 transition-all"
          >
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto shadow-lg">
              {step.icon}
            </div>
            <h3 className="text-xl font-semibold">{step.title}</h3>
            <p className="text-gray-600">{step.description}</p>
          </motion.div>
        ))}
      </section>

      {/* Timeline Section */}
      <section className="relative py-16 z-10">
        <h2 className="text-4xl font-bold text-center mb-12">Project Workflow Timeline</h2>
        <div className="relative space-y-8 md:space-y-0 md:grid md:grid-cols-5 gap-4">
          {timelineSteps.map((step, index) => (
            <motion.div
              key={index}
              className="relative group p-6 bg-white rounded-lg shadow-lg border-2 border-gray-200 cursor-pointer transition-all hover:border-red-500"
              whileHover={{ scale: 1.05 }}
            >
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                {step.icon}
              </div>
              <h3 className="text-xl font-semibold">{step.title}</h3>
              <p className="text-gray-600 mt-2">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative bg-red-100 text-black rounded-2xl p-12 text-center space-y-6 shadow-lg z-10">
        <h2 className="text-4xl font-bold">Ready to Transform Your Content?</h2>
        <p className="text-xl opacity-90">
          Join thousands of content creators who are scaling their content production.
        </p>
        <center>
          <motion.div>
            <Button
              variant="outline"
              size="lg"
              className="!text-white bg-red-500 border-red-500 hover:bg-red-700 transition-all"
            >
              Start Free Trial
            </Button>
          </motion.div>
        </center>
      </section>
    </div>
  );
};

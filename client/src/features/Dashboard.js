import React, { useState, useCallback } from 'react';
import { Upload, X, Image } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function Dashboard({isDark}) {
  const [mainImage, setMainImage] = useState(null);
  const [secondaryImage, setSecondaryImage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // Upload main image via form data (for file input and drag & drop)
  const uploadMainImage = async (file) => {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/uploads/main/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Main image upload error:', error);
      throw error;
    }
  };

  // Upload secondary image via form data (for file input and drag & drop)
  const uploadSecondaryImage = async (file) => {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/uploads/secondary/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Secondary image upload error:', error);
      throw error;
    }
  };

  // Upload main image via base64 (for paste functionality)
  const uploadMainImageBase64 = async (base64Data, filename = null) => {
    try {
      const response = await fetch(`${API_URL}/api/uploads/main/upload/base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          filename: filename || `main-pasted-${Date.now()}.png`
        }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Main image base64 upload error:', error);
      throw error;
    }
  };

  // Upload secondary image via base64 (for paste functionality)
  const uploadSecondaryImageBase64 = async (base64Data, filename = null) => {
    try {
      const response = await fetch(`${API_URL}/api/uploads/secondary/upload/base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          filename: filename || `secondary-pasted-${Date.now()}.png`
        }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Secondary image base64 upload error:', error);
      throw error;
    }
  };

  const handleImageUpload = useCallback(async (file, type) => {
    if (file && file.type.startsWith('image/')) {
      setIsUploading(true);
      try {
        let result;
        
        // Upload to appropriate endpoint based on type
        if (type === 'main') {
          result = await uploadMainImage(file);
        } else {
          result = await uploadSecondaryImage(file);
        }

        // Create image data for local preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const imageData = {
            file: file,
            url: e.target.result,
            name: file.name,
            upload_id: result.upload_id,
            file_id: result.file_id,
            file_size: file.size
          };
          
          if (type === 'main') {
            setMainImage(imageData);
          } else {
            setSecondaryImage(imageData);
          }
        };
        reader.readAsDataURL(file);

        console.log(`${type} image uploaded successfully:`, result);
        
      } catch (error) {
        console.error(`${type} image upload failed:`, error);
        // Show error to user
        alert(`Upload failed: ${error.message}`);
      } finally {
        setIsUploading(false);
      }
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e, type) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleImageUpload(files[0], type);
    }
  }, [handleImageUpload]);

  const handleFileInput = useCallback((e, type) => {
    const file = e.target.files[0];
    if (file) {
      handleImageUpload(file, type);
    }
  }, [handleImageUpload]);

  const handlePaste = useCallback(async (e, type) => {
    e.preventDefault();
    const items = Array.from(e.clipboardData.items);
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          setIsUploading(true);
          try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
              const base64Data = e.target.result;
              
              let result;
              const filename = `pasted-image-${Date.now()}.png`;
              
              // Upload to appropriate endpoint based on type
              if (type === 'main') {
                result = await uploadMainImageBase64(base64Data, filename);
              } else {
                result = await uploadSecondaryImageBase64(base64Data, filename);
              }

              // Create image data for local preview
              const imageData = {
                file: new File([blob], filename, { type: blob.type }),
                url: base64Data,
                name: filename,
                upload_id: result.upload_id,
                file_id: result.file_id,
                file_size: blob.size
              };
              
              if (type === 'main') {
                setMainImage(imageData);
              } else {
                setSecondaryImage(imageData);
              }

              console.log(`${type} image pasted and uploaded successfully:`, result);
              setIsUploading(false);
            };
            reader.readAsDataURL(blob);
            
          } catch (error) {
            console.error(`${type} image paste upload failed:`, error);
            alert(`Paste upload failed: ${error.message}`);
            setIsUploading(false);
          }
        }
        break; // Only handle the first image found
      }
    }
  }, []);

  const removeImage = useCallback((type) => {
    if (type === 'main') {
      setMainImage(null);
    } else {
      setSecondaryImage(null);
    }
  }, []);

  const handleCompareScreenshots = async () => {
    if (mainImage && secondaryImage) {
      try {
        // Here you can implement comparison logic
        // For now, just log the image data
        console.log('Comparing screenshots:', {
          main: mainImage,
          secondary: secondaryImage
        });
        
        // You could call a comparison API endpoint here
        // const comparisonResult = await fetch(`${API_URL}/api/compare`, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({
        //     main_file_id: mainImage.file_id,
        //     secondary_file_id: secondaryImage.file_id
        //   })
        // });
        
        alert('Comparison functionality will be implemented here!');
      } catch (error) {
        console.error('Comparison failed:', error);
        alert('Comparison failed. Please try again.');
      }
    }
  };

  const UploadField = ({ title, type, image, onDrop, onFileInput, onRemove, handlePaste }) => (
    <div className="flex flex-col space-y-3">
      <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{title}</label>
      
      {!image ? (
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer focus:outline-none focus:ring-2 ${
            isDark 
              ? 'border-gray-600 hover:border-gray-500 bg-gray-800 focus:ring-cyan-500' 
              : 'border-gray-300 hover:border-gray-400 bg-white focus:ring-blue-500'
          } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={handleDragOver}
          onDrop={(e) => onDrop(e, type)}
          onPaste={(e) => handlePaste(e, type)}
          onClick={() => !isUploading && document.getElementById(`file-input-${type}`).click()}
          tabIndex={0}
        >
          <Upload className={`mx-auto h-12 w-12 ${isDark ? 'text-gray-500' : 'text-gray-400'} ${isUploading ? 'animate-pulse' : ''}`} />
          <div className="mt-4">
            <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {isUploading ? (
                <span className="font-medium">Uploading...</span>
              ) : (
                <>
                  <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>Click to upload</span>, drag and drop, or <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>paste (Ctrl+V)</span>
                </>
              )}
            </p>
            <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>PNG, JPG, GIF up to 10MB</p>
          </div>
          
          <input
            id={`file-input-${type}`}
            type="file"
            className="hidden"
            accept="image/*"
            onChange={(e) => onFileInput(e, type)}
            disabled={isUploading}
          />
        </div>
      ) : (
        <div className={`relative border rounded-lg p-4 ${
          isDark 
            ? 'border-gray-600 bg-gray-800' 
            : 'border-gray-200 bg-white'
        }`}>
          <button
            onClick={() => onRemove(type)}
            className={`absolute top-2 right-2 z-10 p-1 rounded-full transition-colors ${
              isDark 
                ? 'bg-red-900 hover:bg-red-800 text-red-400' 
                : 'bg-red-100 hover:bg-red-200 text-red-600'
            }`}
          >
            <X size={16} />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <img
                src={image.url}
                alt={image.name}
                className="h-20 w-20 object-cover rounded border"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-medium truncate ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                {image.name}
              </p>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {(image.file_size / 1024 / 1024).toFixed(2)} MB
              </p>
              {image.upload_id && (
                <p className={`text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                  ✓ Uploaded successfully
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              <Image className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-500'}`} />
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dashboard</h1>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Upload and compare your screenshots</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <UploadField
          title="Main Screenshot"
          type="main"
          image={mainImage}
          onDrop={handleDrop}
          onFileInput={handleFileInput}
          onRemove={removeImage}
          handlePaste={handlePaste}
        />
        
        <UploadField
          title="Secondary Screenshot"
          type="secondary"
          image={secondaryImage}
          onDrop={handleDrop}
          onFileInput={handleFileInput}
          onRemove={removeImage}
          handlePaste={handlePaste}
        />
      </div>

      {mainImage && secondaryImage && (
        <div className={`mt-8 pt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={handleCompareScreenshots}
              className={`px-6 py-2 text-white font-medium rounded-lg transition-colors ${
                isDark 
                  ? 'bg-cyan-600 hover:bg-cyan-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              Compare Screenshots
            </button>
            <button 
              onClick={() => {
                setMainImage(null);
                setSecondaryImage(null);
              }}
              className={`px-6 py-2 font-medium rounded-lg transition-colors ${
                isDark 
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              Clear All
            </button>
          </div>
        </div>
      )}

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <div className={`p-6 rounded-lg border shadow-sm ${
          isDark 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Total Comparisons</h3>
          <p className={`text-3xl font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>24</p>
        </div>
        
        <div className={`p-6 rounded-lg border shadow-sm ${
          isDark 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>This Week</h3>
          <p className={`text-3xl font-bold ${isDark ? 'text-green-400' : 'text-green-600'}`}>8</p>
        </div>
        
        <div className={`p-6 rounded-lg border shadow-sm ${
          isDark 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Success Rate</h3>
          <p className={`text-3xl font-bold ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>92%</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
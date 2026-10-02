/**
 * @file CropSelector.tsx
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */

﻿type CropSelectorProps = {
  selectedCrop: string;
  onCropChange: (crop: string) => void;
};

const crops = [
  'Tomato', 'Potato', 'Rice', 'Corn', 'Brinjal', 
  'Cabbage', 'Capsicum', 'Carrot', 'Cauliflower', 
  'Chilli', 'Lettuce', 'Mushroom', 'Radish', 
  'Rose', 'Tea', 'Anthurium'
];

export default function CropSelector({ selectedCrop, onCropChange }: CropSelectorProps) {
  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        Select Crop
      </div>
      
      <select 
        className="crop-select"
        value={selectedCrop}
        onChange={(e) => onCropChange(e.target.value)}
      >
        {crops.map((crop) => (
          <option key={crop} value={crop.toLowerCase()}>
            {crop}
          </option>
        ))}
      </select>
    </div>
  );
}

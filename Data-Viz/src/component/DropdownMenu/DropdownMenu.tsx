import React, { useState } from "react";

interface DropdownMenuProps {
  options: string[];
  onSelect: (option: string) => void;
}

const DropdownStyle = {
  dropdown: {
    fontFamily: "Work Sans, Helvetica",
    fontSize: "14px",
    fontStyle: "normal",
    fontWeight: 400,
    letterSpacing: "0.08px",
    lineHeight: "20px",
  },
  dropdownToggle: {
    fontFamily: "Work Sans, Helvetica",
    fontSize: "14px",
    fontStyle: "normal",
    fontWeight: 500,
    letterSpacing: "0.4px",
    lineHeight: "20px",
    color: "rgba(97, 100, 107, 1)",
  },
  dropdownMenu: {
    backgroundColor: "rgba(255, 255, 255, 1)",
    color: "rgba(175, 177, 182, 1)",
  },
};

const DropdownMenu: React.FC<DropdownMenuProps> = ({ options, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleSelect = (option: string) => {
    setSelectedOption(option);
    onSelect(option);
    setIsOpen(false);
  };

  return (
    <div style={DropdownStyle.dropdown}>
      <div
        style={DropdownStyle.dropdownToggle}
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedOption || "Select an option"}
      </div>
      {isOpen && (
        <div style={DropdownStyle.dropdownMenu}>
          {options.map((option) => (
            <div
              key={option}
              onClick={() => handleSelect(option)}
              style={{ padding: "8px", cursor: "pointer" }}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

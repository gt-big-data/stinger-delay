import React, { useState, useRef, useEffect } from "react";
import styles from "./DropdownMenu.module.css";

interface DropdownOption {
  value: string;
  label: string;
}

interface DropdownMenuProps {
  options: DropdownOption[];
  onSelect: (option: DropdownOption) => void;
  placeholder?: string;
  selectedValue?: string;
}

const DropdownMenu: React.FC<DropdownMenuProps> = ({
  options,
  onSelect,
  placeholder = "Select an option",
  selectedValue,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const handleSelect = (option: DropdownOption) => {
    onSelect(option);
    setIsOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const selectedOption = options.find((opt) => opt.value === selectedValue);

  return (
    <div className={styles.dropdown} ref={ref}>
      <div
        className={styles.toggle}
        onClick={() => setIsOpen((prev) => !prev)}
        role="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {selectedOption ? selectedOption.label : placeholder}
      </div>

      {isOpen && (
        <div className={styles.menu} role="listbox">
          {options.map((option) => (
            <div
              key={option.value}
              className={styles.option}
              role="option"
              onClick={() => handleSelect(option)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DropdownMenu;

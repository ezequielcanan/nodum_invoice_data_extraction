import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AiOutlineCaretDown, AiOutlineCaretUp } from 'react-icons/ai';

const Dropdown = ({text, children, }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className='flex flex-col gap-y-4 items-center justify-center w-full my-2'>
      <button onClick={() => setIsOpen(!isOpen)} className="text-white text-lg bg-first p-4 rounded-md w-full flex gap-2 items-center justify-between">{text} {isOpen ? <AiOutlineCaretUp/> : <AiOutlineCaretDown/>}</button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.5 }}
            className="overflow-hidden w-full"
          >
            <div className="flex flex-col gap-y-2">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dropdown;

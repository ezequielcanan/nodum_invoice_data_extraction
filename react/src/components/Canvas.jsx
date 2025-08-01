import React, { useRef, useState, useEffect } from 'react';

function Canvas({ image, magnet, actualFile, imageName, passToPercentageX, passToPercentageY, passToValueX, passToValueY, imageDimensions, setFieldCompleted, rectangles, setRectangles, field, files, setField, setImageDimensions, fields, setFields }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false)
  const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
  const [undoStack, setUndoStack] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const [clipboard, setClipboard] = useState({})
  const [currentMousePos, setCurrentMousePos] = useState({ x: 0, y: 0 });

  const drawImageAndRectangles = (ctx, img) => {
    ctx.clearRect(0, 0, imageDimensions[0], imageDimensions[1]);
    ctx.drawImage(img, 0, 0, imageDimensions[0], imageDimensions[1]);
    rectangles.forEach(rect => {
      const isFocused = rect.field == fields?.find(f => f.focused)?.field
      if (actualFile == rect.file) {
        ctx.strokeStyle = isFocused ? 'red' : "green";
        ctx.lineWidth = 2
        ctx.strokeRect(passToValueX(rect.x), passToValueY(rect.y), passToValueX(rect.width), passToValueY(rect.height));
        ctx.fillStyle = 'black';
        ctx.fillText(rect?.text, passToValueX(rect.x), passToValueY(rect.y + rect.height) + 10);
      }
    });
  };

  useEffect(() => {
    const img = new Image();
    img.src = image;
    img.onload = () => {
      setImageLoaded(img)
      setImageDimensions([img.width, img.height])
    }
  }, [actualFile, files])

  useEffect(() => {
    if (imageLoaded) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      drawImageAndRectangles(ctx, imageLoaded);
    }
  }, [imageLoaded, image, rectangles, fields])


  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey) {
        switch (e.key) {
          case "z":
            handleUndo();
            break
          case "y":
            handleRedo()
            break
          case "c":
            const clipCoords = rectangles?.find(r => r.field == field.field)
            if (clipCoords) {
              setClipboard({...clipCoords, y: Number(clipCoords?.y) + Number(clipCoords?.height)})
            } else {
              setClipboard({})
            }
            break
          case "v":
            if (clipboard) {
              const newRectangle = {...clipboard, field: field.field, new: true, text: field.text, row: field.row || false, column: field.column || false, file: actualFile, imageName}
              const existingRectangle = rectangles.findIndex(r => r.field == field.field)
              existingRectangle != -1 ? rectangles.splice(existingRectangle, 1) : null
              
              setRectangles([...rectangles, newRectangle])
              setFieldCompleted(field.field)
              //setField(getNext(field.field))
              setRedoStack([])
            }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [undoStack, redoStack, field]);

  
  const handleUndo = () => {
    if (rectangles.length > 0) {
      fields[fields.findIndex(f => rectangles[rectangles.length - 1].text == f.text)].completed = false
      setFields([...fields])
      const newRectangles = rectangles.slice(0, -1);
      const lastRectangle = rectangles[rectangles.length - 1];
      setUndoStack([...undoStack, lastRectangle]);
      setRectangles(newRectangles);
      setRedoStack([]);
    }
  };

  const handleRedo = () => {
    if (undoStack.length > 0) {
      const newRectangles = [...rectangles, undoStack[undoStack.length - 1]];
      setRectangles(newRectangles);
      setUndoStack(undoStack.slice(0, -1));
    }
  };

  const snapToGrid = (x, y, tolerance = (magnet ? 20 : 0)) => {
    let snappedX = x;
    let snappedY = y;
    let minDistance = tolerance;
  
    for (let rect of rectangles) {
      // Define puntos a considerar: vértices y aristas
      const points = [
        { x: rect.x, y: rect.y }, // top-left
        { x: rect.x + rect.width, y: rect.y }, // top-right
        { x: rect.x, y: rect.y + rect.height }, // bottom-left
        { x: rect.x + rect.width, y: rect.y + rect.height }, // bottom-right
      ];
  
      // Considerar las aristas
      if (y >= rect.y && y <= rect.y + rect.height) {
        points.push({ x: rect.x, y: y }); // left edge
        points.push({ x: rect.x + rect.width, y: y }); // right edge
      }
      if (x >= rect.x && x <= rect.x + rect.width) {
        points.push({ x: x, y: rect.y }); // top edge
        points.push({ x: x, y: rect.y + rect.height }); // bottom edge
      }
  
      // Calcular la distancia mínima a los puntos
      for (let point of points) {
        const distance = Math.sqrt((x - point.x) ** 2 + (y - point.y) ** 2);
        if (distance < minDistance) {
          snappedX = point.x;
          snappedY = point.y;
          minDistance = distance;
        }
      }
    }
  
    return { x: snappedX, y: snappedY };
  };
  

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const { x, y } = snapToGrid(e.clientX - rect.left, e.clientY - rect.top);
    setStartPoint({
      x,
      y
    });
    setIsDrawing(true);
  };


  const handleMouseUp = (e) => {
    if (isDrawing) {
      const rect = canvasRef.current.getBoundingClientRect();
      let { x, y } = snapToGrid(e.clientX - rect.left, e.clientY - rect.top);
      const endPoint = {
        x,
        y
      };
      const newRect = {
        new: true,
        x: passToPercentageX(Math.round((startPoint.x))),
        y: passToPercentageY(Math.round((startPoint.y))),
        width: passToPercentageX(Math.round((endPoint.x - startPoint.x))),
        height: passToPercentageY(Math.round((endPoint.y - startPoint.y))),
        text: field.text,
        row: field.row || false,
        column: field.column || false,
        file: actualFile,
        imageName,
        field: field.field
      };

      if (newRect.width < 0) {
        newRect.x = endPoint.x
        newRect.width = -newRect.width
      }

      if (newRect.height < 0) {
        newRect.y = endPoint.y
        newRect.height = -newRect.height
      }

      const existingRectangle = rectangles.findIndex(r => r.text == field.text)
      existingRectangle != -1 ? rectangles.splice(existingRectangle, 1) : null

      setFieldCompleted(field.field)
      //setField(getNext(field.field))
      setRectangles([...rectangles, newRect]);
      setIsDrawing(false);
      setRedoStack([])
    }
  };

  const handleMouseMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    let { x, y } = snapToGrid(e.clientX - rect.left, e.clientY - rect.top);

    setCurrentMousePos({ x, y });

    if (isDrawing) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      const endPoint = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };

      const img = new Image();
      img.src = image;
      img.onload = () => {
        drawImageAndRectangles(ctx, img);
        ctx.strokeStyle = 'red';
        ctx.strokeRect(startPoint.x, startPoint.y, endPoint.x - startPoint.x, endPoint.y - startPoint.y);
      };
    }
  };

  return (
    <>
      {imageLoaded && <canvas
        ref={canvasRef}
        width={imageDimensions[0]}
        height={imageDimensions[1]}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseMove={handleMouseMove}
        style={{ border: '1px solid black' }}
      />}
    </>
  )
}

export default Canvas;

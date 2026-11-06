// Normalize pointer coordinates independently of screen resolution.
export function normalizedPoint(x,y,width,height) {
  if(![x,y,width,height].every(Number.isFinite)||width<=0||height<=0) throw new Error("Invalid drawing bounds.");
  return {x:Math.max(0,Math.min(1,x/width)),y:Math.max(0,Math.min(1,y/height))};
}
// Paint bounded normalized strokes at preview or export resolution.
export function paintStrokes(context,strokes,width,height,color) {
  if(strokes.length>50||strokes.some(stroke=>stroke.length>2000)) throw new Error("Maximum 50 strokes with 2,000 points each.");
  context.strokeStyle=color;context.fillStyle=color;context.lineWidth=height/100;context.lineCap="round";context.lineJoin="round";
  for(const stroke of strokes) {
    if(!stroke.length) continue;
    if(stroke.some(point=>!Number.isFinite(point.x)||!Number.isFinite(point.y)||point.x<0||point.x>1||point.y<0||point.y>1)) throw new Error("Invalid drawing coordinates.");
    context.beginPath();context.moveTo(stroke[0].x*width,stroke[0].y*height);
    for(const point of stroke.slice(1)) context.lineTo(point.x*width,point.y*height);
    if(stroke.length===1){context.arc(stroke[0].x*width,stroke[0].y*height,context.lineWidth/2,0,2*Math.PI);context.fill();}
    else context.stroke();
  }
}


from feature_extraction_server.core.model import Model


class DetrResnet101(Model):

    def _load_model(self):
        global torch
        import torch
        from transformers import DetrImageProcessor, DetrForObjectDetection
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-101")
        self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-101")

    def object_detection(self, image, config={}):
        scores = []
        labels = []
        boxes = []
        for single_image in image:
            single_image = single_image.to_numpy()
            inputs = self.processor(images=single_image, return_tensors="pt")
            outputs = self.model(**inputs, **config)

            # convert outputs (bounding boxes and class logits) to COCO API
            # let's only keep detections with score > 0.9
            target_sizes = torch.tensor([single_image.size[::-1]])
            single_results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]
            scores.append(single_results['scores'].tolist())
            labels.append([self.model.config.id2label[int(i)] for i in single_results['labels']])
            boxes.append(single_results['boxes'].tolist())
        
        return {"scores": scores, "labels": labels, "boxes": boxes}
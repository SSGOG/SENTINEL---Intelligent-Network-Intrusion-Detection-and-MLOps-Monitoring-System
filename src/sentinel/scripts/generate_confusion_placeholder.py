import os
import matplotlib.pyplot as plt
import numpy as np

# Create a simple 2x2 confusion matrix image as a placeholder
cm = np.array([[21231, 120], [85, 950]])
labels = ['BENIGN', 'MALICIOUS']
fig, ax = plt.subplots(figsize=(4,4))
im = ax.imshow(cm, cmap='viridis')
ax.set_xticks([0,1])
ax.set_yticks([0,1])
ax.set_xticklabels(labels)
ax.set_yticklabels(labels)
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, f"{cm[i,j]:,}", ha='center', va='center', color='white')
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')
plt.title('Confusion Matrix Placeholder')
plt.colorbar(im, ax=ax)
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'confusion_matrix_placeholder.png'))
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.tight_layout()
plt.savefig(output_path, dpi=150, transparent=False)
print(f"Placeholder confusion matrix saved to {output_path}")

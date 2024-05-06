from django.http import JsonResponse
from . import utils

# Create your views here.
def create_vm(request):
    if request.method == 'POST':
        node = request.POST.get('node')
        vmid = request.POST.get('vmid')
        config = {
            'memory': request.POST.get('memory'),
            'cores': request.POST.get('cores'),
            'net0': 'virtio,bridge=vmbr0',
            # Add other configurations as needed
        }
        result = utils.create_vm(node, vmid, config)
        return JsonResponse({'status': 'success', 'data': result})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
def clone_vm(request):
    if request.method == 'POST':
        node = request.POST.get('node')
        vmid = request.POST.get('vmid')
        newid = request.POST.get('newid')
        config = {
            'name': request.POST.get('name', ''),  # Default empty if not provided
            'storage': request.POST.get('storage', '')  # Default empty if not provided
            # Include other options as needed
        }
        result = utils.clone_vm(node, vmid, newid, config)
        return JsonResponse({'status': 'success', 'data': result})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
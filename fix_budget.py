import re

with open('budgetplaning.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old form submission handler
old_js = """        // Form submission
        document.getElementById('budget-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const category = document.getElementById('category-select').value;
            const amount = document.getElementById('budget-amount').value;
            const notes = document.getElementById('budget-notes').value;
            
            if (category && amount) {
                alert('Budget added successfully!\nCategory: ' + category + '\nAmount: Rp ' + parseInt(amount).toLocaleString('id-ID'));
                closeBudgetModal();
                // Reset form
                this.reset();
            }
        });"""

new_js = """        // Category mapping for dropdown values
        const categoryMap = {
            'uangmakan': { name: 'Food/Dining', icon: 'utensils', color: 'orange' },
            'transportasi': { name: 'Transportasi', icon: 'car', color: 'blue' },
            'paketkuota': { name: 'Paket Kuota', icon: 'wifi', color: 'cyan' },
            'shoppinghiburan': { name: 'Shopping & Hiburan', icon: 'shopping-bag', color: 'pink' },
            'tabungan': { name: 'Tabungan', icon: 'piggy-bank', color: 'green' }
        };

        // Handle category select change to show/hide custom name input
        function handleCategoryChange() {
            const select = document.getElementById('category-select');
            const otherContainer = document.getElementById('other-name-container');
            if (select.value === 'other') {
                otherContainer.classList.remove('hidden');
            } else {
                otherContainer.classList.add('hidden');
            }
        }

        // Form submission - updates budgetData and refreshes display
        document.getElementById('budget-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const categoryValue = document.getElementById('category-select').value;
            const amount = parseInt(document.getElementById('budget-amount').value);

            if (!categoryValue || !amount || amount <= 0) {
                alert('Please select a category and enter a valid amount.');
                return;
            }

            let categoryName;
            let categoryMeta;

            if (categoryValue === 'other') {
                categoryName = document.getElementById('other-name').value.trim();
                if (!categoryName) {
                    alert('Please enter a custom category name.');
                    return;
                }
                categoryMeta = { icon: 'tag', color: 'gray' };
            } else {
                categoryMeta = categoryMap[categoryValue];
                categoryName = categoryMeta.name;
            }

            // Check if category already exists
            const existingIndex = budgetData.categories.findIndex(cat => cat.name === categoryName);
            if (existingIndex >= 0) {
                // Update existing category budget
                budgetData.categories[existingIndex].budget = amount;
            } else {
                // Add new category
                budgetData.categories.push({
                    name: categoryName,
                    spent: 0,
                    budget: amount,
                    icon: categoryMeta.icon,
                    color: categoryMeta.color
                });
            }

            // Recalculate total budget as sum of all category budgets
            budgetData.totalBudget = budgetData.categories.reduce((sum, cat) => sum + cat.budget, 0);

            // Refresh display
            updateBudgetCalculations();

            alert('Budget added successfully!\\nCategory: ' + categoryName + '\\nAmount: Rp ' + amount.toLocaleString('id-ID'));
            closeBudgetModal();
            this.reset();
            document.getElementById('other-name-container').classList.add('hidden');
        });"""

if old_js in content:
    content = content.replace(old_js, new_js)
    with open('budgetplaning.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Form submission handler replaced.')
else:
    print('ERROR: Could not find old_js block.')
    idx = content.find('// Form submission')
    if idx >= 0:
        print('Found // Form submission at index', idx)
        print('Snippet:', repr(content[idx:idx+500]))
    else:
        print('Could not even find // Form submission')


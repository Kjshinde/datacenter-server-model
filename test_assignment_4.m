%% EEE 498/591 - Assignment 4 Solution
% This script solves both parts of Assignment 4.
% Part A: Simulates CPU/GPU performance for each customer.
% Part B: Calculates max and min net profit for the retrofitted data center.

clear;
clc;
format compact;

%% ========================================================================
%  1. DATA INITIALIZATION (FROM SLIDES)
% =========================================================================

% --- Processor Configurations ---
% Data from slide 19 [cite: 343]
cpuConfig.name = 'Intel Xeon 6774P';
cpuConfig.maxCores = 64;
cpuConfig.maxFrequency = 2500e6; % Hz
cpuConfig.TDP = 350; % Watts

gpuConfig.name = 'NVIDIA B100';
gpuConfig.maxCores = 16896;
gpuConfig.maxFrequency = 1900e6; % Hz
gpuConfig.TDP = 700; % Watts

% --- Customer Compute Loads ---
% [cite_start]% Data from slide 18 [cite: 338]
% Customer A
customerA.cpu.init_instr = 200000;
customerA.cpu.main_instr = 0;
customerA.cpu.result_instr = 100000;
customerA.cpu.init_load = 0.5;
customerA.cpu.main_load = 0;
customerA.cpu.result_load = 0.5;

customerA.gpu.init_instr = 20000;
customerA.gpu.main_instr = 20e12; % 20 TOPS
customerA.gpu.result_instr = 10000;
customerA.gpu.init_load = 0.1;
customerA.gpu.main_load = 0.85;
customerA.gpu.result_load = 0.1;

% Customer B
customerB.cpu.init_instr = 500000;
customerB.cpu.main_instr = 0;
customerB.cpu.result_instr = 100000;
customerB.cpu.init_load = 0.5;
customerB.cpu.main_load = 0;
customerB.cpu.result_load = 0.5;

customerB.gpu.init_instr = 40000;
customerB.gpu.main_instr = 2000e12; % 2000 TOPS
customerB.gpu.result_instr = 10000;
customerB.gpu.init_load = 0.1;
customerB.gpu.main_load = 0.80;
customerB.gpu.result_load = 0.1;

% Customer C
customerC.cpu.init_instr = 1000000;
customerC.cpu.main_instr = 0;
customerC.cpu.result_instr = 100000;
customerC.cpu.init_load = 0.5;
customerC.cpu.main_load = 0;
customerC.cpu.result_load = 0.5;

customerC.gpu.init_instr = 50000;
customerC.gpu.main_instr = 8000e12; % 8000 TOPS
customerC.gpu.result_instr = 10000;
customerC.gpu.init_load = 0.1;
customerC.gpu.main_load = 0.75;
customerC.gpu.result_load = 0.1;

customers = {customerA, customerB, customerC};

% --- Financial and Data Center Parameters ---
% [cite_start]% Data from slides 17 and 20 [cite: 327, 345]
dc.numRacks = 100;
dc.hoursPerMonth = 720;
dc.maintenancePerRack = 500; % $/month
dc.overheadPerRack = 100; % $/month
dc.kWh_rate = 0.20; % $/kWh

customerProfiles(1).name = 'A';
customerProfiles(1).revenue_rate = 10; % $/hour
customerProfiles(2).name = 'B';
customerProfiles(2).revenue_rate = 20; % $/hour
customerProfiles(3).name = 'C';
customerProfiles(3).revenue_rate = 40; % $/hour


%% ========================================================================
%  PART A: PERFORMANCE SIMULATION
% =========================================================================
fprintf('## Part A: Performance Simulation Results ##\n\n');
fprintf('%-12s | %-15s | %-15s\n', 'Customer', 'Exec Time (ms)', 'Energy (Joules)');
fprintf('--------------------------------------------------\n');

performanceResults = struct('name', {}, 'time', {}, 'energy', {});

for i = 1:length(customers)
    % Simulate performance for each customer
    result = simulatePerformance(customers{i}, cpuConfig, gpuConfig);
    
    % Store and display results
    performanceResults(i).name = customerProfiles(i).name;
    performanceResults(i).time = result.totalTime;
    performanceResults(i).energy = result.totalEnergy;
    
    fprintf('%-12s | %-15.4f | %-15.2f\n', ...
        performanceResults(i).name, performanceResults(i).time * 1000, performanceResults(i).energy);
end


%% ========================================================================
%  PART B: FINANCIAL ANALYSIS (MAX & MIN PROFIT)
% =========================================================================
fprintf('\n\n## Part B: Financial Analysis ##\n');

% --- Max Profit Scenario: 100 Racks for Customer C (highest revenue) ---
maxProfitScenario.rackAllocation = [0, 0, 100]; % [Racks_A, Racks_B, Racks_C]
maxProfitScenario.name = 'Max Profit (100% Customer C)';
maxProfitResults = calculateProfit(maxProfitScenario, performanceResults, customerProfiles, dc);

% --- Min Profit Scenario: 100 Racks for Customer A (lowest revenue) ---
minProfitScenario.rackAllocation = [100, 0, 0]; % [Racks_A, Racks_B, Racks_C]
minProfitScenario.name = 'Min Profit (100% Customer A)';
minProfitResults = calculateProfit(minProfitScenario, performanceResults, customerProfiles, dc);

% --- Display Financial Results ---
fprintf('\n--- Maximum Profit Scenario ---\n');
displayFinancials(maxProfitResults);

fprintf('\n--- Minimum Profit Scenario ---\n');
displayFinancials(minProfitResults);


%% ========================================================================
%  SUPPORTING FUNCTIONS
% =========================================================================

function result = simulatePerformance(load, cpu, gpu)
    % This function calculates the total time and energy for one transaction.

    % --- CPU Calculations ---
    cpu_time_init = load.cpu.init_instr / (cpu.maxCores * cpu.maxFrequency);
    cpu_time_main = 0; % No main instructions for CPU
    cpu_time_result = load.cpu.result_instr / (cpu.maxCores * cpu.maxFrequency);
    
    cpu_energy_init = cpu.TDP * load.cpu.init_load * cpu_time_init;
    cpu_energy_main = 0;
    cpu_energy_result = cpu.TDP * load.cpu.result_load * cpu_time_result;

    % --- GPU Calculations ---
    gpu_time_init = load.gpu.init_instr / (gpu.maxCores * gpu.maxFrequency);
    gpu_time_main = load.gpu.main_instr / (gpu.maxCores * gpu.maxFrequency);
    gpu_time_result = load.gpu.result_instr / (gpu.maxCores * gpu.maxFrequency);

    gpu_energy_init = gpu.TDP * load.gpu.init_load * gpu_time_init;
    gpu_energy_main = gpu.TDP * load.gpu.main_load * gpu_time_main;
    gpu_energy_result = gpu.TDP * load.gpu.result_load * gpu_time_result;

    % --- Combine phase results ---
    time_init = max(cpu_time_init, gpu_time_init);
    energy_init = cpu_energy_init + gpu_energy_init;

    time_main = gpu_time_main; % CPU is idle
    energy_main = gpu_energy_main;

    time_result = max(cpu_time_result, gpu_time_result);
    energy_result = cpu_energy_result + gpu_energy_result;
    
    % --- Final Totals ---
    result.totalTime = time_init + time_main + time_result; % in seconds
    result.totalEnergy = energy_init + energy_main + energy_result; % in Joules
end

function results = calculateProfit(scenario, perf, profiles, dc)
    % This function calculates the net profit for a given rack allocation scenario.
    
    totalRevenue = 0;
    totalPowerCost = 0;
    
    for i = 1:length(scenario.rackAllocation)
        numRacks = scenario.rackAllocation(i);
        if numRacks == 0
            continue;
        end
        
        % Calculate revenue for this customer type
        revenue_rate = profiles(i).revenue_rate;
        customerRevenue = numRacks * dc.hoursPerMonth * revenue_rate;
        totalRevenue = totalRevenue + customerRevenue;
        
        % Calculate power cost for this customer type
        time_per_txn = perf(i).time;
        energy_per_txn = perf(i).energy; % Joules
        
        txn_per_hour = 3600 / time_per_txn;
        
        % Joules/hr -> kWh/month
        joules_per_month = energy_per_txn * txn_per_hour * dc.hoursPerMonth * numRacks;
        kWh_per_month = joules_per_month / (3.6e6); % 3.6e6 Joules in 1 kWh
        
        customerPowerCost = kWh_per_month * dc.kWh_rate;
        totalPowerCost = totalPowerCost + customerPowerCost;
    end
    
    % Calculate other fixed costs
    otherCost = dc.numRacks * (dc.maintenancePerRack + dc.overheadPerRack);
    
    % Final profit calculation
    results.name = scenario.name;
    results.totalRevenue = totalRevenue;
    results.powerCost = totalPowerCost;
    results.otherCost = otherCost;
    results.totalCost = totalPowerCost + otherCost;
    results.netProfit = totalRevenue - results.totalCost;
end

function displayFinancials(results)
    fprintf('Scenario: %s\n', results.name);
    fprintf('  Total Monthly Revenue: $%.2f\n', results.totalRevenue);
    fprintf('  Monthly Power Cost:    $%.2f\n', results.powerCost);
    fprintf('  Monthly Other Cost:    $%.2f\n', results.otherCost);
    fprintf('  Total Operating Cost:  $%.2f\n', results.totalCost);
    fprintf('  ----------------------------------\n');
    fprintf('  NET PROFIT:            $%.2f\n', results.netProfit);
end